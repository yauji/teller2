import datetime
import csv
import io
from datetime import timedelta
import codecs
import os
import re
import unicodedata
import logging

from django.shortcuts import render, redirect
from django.utils import timezone

from ..models import Trans, PmethodGroup, Pmethod, CategoryGroup, Category
from .base import (
    CategoryUi,
    TransUi,
    update_balance,
    C_MOVE_ID,
    CATEGORY_ID_MOVE,
    SUICA_KURIKOSHI,
    JACCS_DISCOUNT,
    CATEGORY_ID_TRANSPORTATION,
    PM_JACCS_ID,
    PM_RAKUTENCARD_ID,
    PM_SHINSEI_ID,
    PM_RAKUTENBANK_ID,
    PM_PAYPAYCARD_ID,
    SALARY_MAPPING_FNAME,
    SHINSEI_CATEGORY_MAPPING_FNAME,
    JACCS_CATEGORY_MAPPING_FNAME,
    PAYPAY_CATEGORY_MAPPING_FNAME,
    SALARY_OTHER_ID,
    SHARE_TYPES_SHARE,
)

logger = logging.getLogger(__name__)


# common utils ---------------------------------------------------------------


def _load_keyword_category_mapping(mapping_path):
    """Load keyword->category_id mapping from a text file."""
    if not os.path.exists(mapping_path):
        return []

    mappings = []
    with open(mapping_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            parts = stripped.split(',', 1)
            if len(parts) != 2:
                continue

            keyword = parts[0].strip()
            cid_str = parts[1].strip()

            if not keyword:
                continue

            try:
                cid = int(cid_str)
            except ValueError:
                continue

            mappings.append((keyword, cid, _normalize_for_match(keyword)))

    return mappings


def _resolve_category_from_content(content, default_category, mappings, cache):
    """
    Pick category based on keyword mapping. Returns default_category when no hit.

    cache keeps Category instances keyed by id to avoid repeated DB hits.
    """
    normalized_content = _normalize_for_match(content)
    for keyword, cid, normalized_keyword in mappings:
        if normalized_keyword in normalized_content:
            if cid in cache:
                logger.warning(
                    '[jaccs] matched keyword "%s" -> cid=%s (cached) content="%s"',
                    keyword, cid, content)
                return cache[cid]
            try:
                cache[cid] = Category.objects.get(pk=cid)
                logger.warning(
                    '[jaccs] matched keyword "%s" -> cid=%s for content="%s"',
                    keyword, cid, content)
                return cache[cid]
            except Category.DoesNotExist:
                logger.warning(
                    '[jaccs] mapped category does not exist: cid=%s keyword="%s"',
                    cid, keyword)
                continue

    return default_category


def _clean_amount(val):
    """Digits and minus only; returns empty string when nothing usable."""
    if val is None:
        return ''
    cleaned = re.sub(r'[^\d-]', '', val)
    return cleaned


def _read_uploaded_text(uploaded_file):
    """
    Read uploaded file content as text.

    Tries UTF-8 first, then common Japanese encodings; falls back to UTF-8
    ignoring errors to avoid hard failure.
    """
    raw = uploaded_file.read()
    for enc in ('utf-8', 'cp932', 'shift_jis'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode('utf-8', errors='ignore')


def _normalize_for_match(text):
    """Normalize strings for keyword matching."""
    if text is None:
        return ''
    normalized = unicodedata.normalize('NFKC', text)
    normalized = normalized.lower()
    normalized = re.sub(r'\s+', '', normalized)
    return normalized


def _make_aware(dt):
    """Convert naive datetime to timezone-aware when USE_TZ is on."""
    if dt is None:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_default_timezone())
    return dt


def _split_shinsei_row(row):
    """Split Shinsei bank rows while preserving empty columns when possible."""
    if '\t' in row:
        return [col.strip() for col in row.split('\t')]
    if ',' in row:
        return [col.strip() for col in row.split(',')]
    return [col for col in re.split(r'\s+', row.strip()) if col != '']


def _load_shinsei_mappings(mapping_path):
    """Load Shinsei keyword mappings (supports move-to/move-from)."""
    if not os.path.exists(mapping_path):
        return []

    mappings = []
    with open(mapping_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            parts = [p.strip() for p in stripped.split(',')]
            if len(parts) < 2:
                continue

            keyword = parts[0]
            try:
                cid = int(parts[1])
            except ValueError:
                continue

            move_type = None
            move_category_id = None
            move_method_id = None
            if len(parts) >= 3 and parts[2].lower() in ('move-to', 'move-from'):
                move_type = parts[2].lower()
                if len(parts) >= 4:
                    try:
                        move_method_id = int(parts[3])
                    except ValueError:
                        move_method_id = None
                # category for move patterns is always move category (id=101)
                move_category_id = C_MOVE_ID

            mappings.append({
                'keyword': keyword,
                'category_id': cid,
                'normalized_keyword': _normalize_for_match(keyword),
                'move_type': move_type,
                'move_category_id': move_category_id,
                'move_method_id': move_method_id,
            })

    return mappings


def _match_shinsei_mapping(text, mappings):
    """Return first mapping that matches text."""
    normalized_content = _normalize_for_match(text)
    for m in mappings:
        if m['normalized_keyword'] in normalized_content:
            return m
    return None


# --- suica ----

def suica_upload(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')
    category_list_all = Category.objects.all().order_by('group__order', 'order')

    pmethodgroup_list = PmethodGroup.objects.filter(
        user=request.user).order_by('order')

    pmethod_list = []
    if len(pmethodgroup_list) > 0:
        pmg = pmethodgroup_list[0]
        pmlist = Pmethod.objects.filter(group=pmg).order_by('order')
        pmethod_list.extend(pmlist)

    date = datetime.datetime.now()
    year = date.year

    if request.method == 'GET':
        context = {'pmethodgroup_list': pmethodgroup_list,
                   'pmethod_list': pmethod_list,
                   'categorygroup_list': categorygroup_list,
                   'category_list': category_list_all,
                   'year': year,
                   }
        return render(request, 'trans/suica_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {'pmethodgroup_list': pmethodgroup_list,
                       'pmethod_list': pmethod_list,
                       'categorygroup_list': categorygroup_list,
                       'category_list': category_list_all,
                       'year': year,
                       'error_message': 'File is mandatory.',
                       }
            return render(request, 'trans/suica_upload.html', context)

        f = request.FILES['file']

        with open('tmp_suica.txt', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        f = open('tmp_suica.txt', 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()

        # get default pmethod
        pmid = int(request.POST['pm'])
        pm_default = Pmethod.objects.get(pk=pmid)

        c_transportation = Category.objects.get(pk=CATEGORY_ID_TRANSPORTATION)
        c_move = Category.objects.get(pk=CATEGORY_ID_MOVE)
        c_food = Category.objects.filter(name__icontains='食費').first()
        if c_food is None:
            c_food = c_transportation

        trans_list = []
        tmpid = 1
        for l in contents:
            if len(l.strip()) == 0:
                continue

            splts = l.split('\t')
            # Drop empty columns while keeping order for newer formats.
            parts = [p for p in splts if p.strip() != '']

            # --- date ---
            date_part = None
            # Older format keeps date in splts[1], newer puts it in parts[0]
            if len(splts) > 1 and '/' in splts[1]:
                date_part = splts[1].strip()
            elif len(parts) > 0:
                date_part = parts[0].strip()

            if not date_part:
                continue

            strdate = request.POST['year'] + '/' + date_part
            parsed_date = datetime.datetime.strptime(strdate, '%Y/%m/%d')

            # --- name ---
            if len(splts) >= 6:
                name_parts = splts[2:6]
            elif len(parts) > 1:
                # Newer format: type/from/to are in the middle, amounts at the end
                name_parts = parts[1:-2] if len(parts) > 3 else parts[1:]
            else:
                name_parts = []

            # --- amount ---
            if len(splts) >= 8:
                expense_field = splts[7]
            elif len(parts) > 0:
                expense_field = parts[-1]
            else:
                expense_field = ''

            expense = expense_field.replace('\n', '').replace(
                ',', '').replace('+', '').replace('\\', '').replace('¥', '')

            if len(expense) != 0:
                sign = -1 if expense.startswith('+') else 1
                expense_clean = re.sub(r'[^\d]', '', expense)
                if expense_clean == '':
                    continue
                expense_value = int(expense_clean) * sign
            else:
                continue

            str0 = ''
            if len(splts) >= 2:
                str0 = splts[1].strip()
            elif len(parts) >= 2:
                str0 = parts[1].strip()

            # skip carry-over rows
            if str0 == "繰":
                continue

            # build name including 2nd column info
            name_with_col2 = ''.join(name_parts + [str0]).strip()
            name = name_with_col2 if name_with_col2 else ''.join(name_parts).strip()

            def _add_trans(amount, category, pmethod):
                nonlocal tmpid
                trans = TransUi()
                trans.id = tmpid
                tmpid += 1
                trans.date = parsed_date
                trans.name = name
                trans.expense = amount
                trans.category = category
                trans.pmethod = pmethod
                # check same trans across pmethods
                checktranslist = Trans.objects.filter(
                    date=trans.date, expense=trans.expense, user=request.user)
                if len(checktranslist) > 0:
                    trans.selected = False
                trans_list.append(trans)

            col2_val = str0.strip()
            if col2_val in ["入", "定", "精", "ﾊﾞｽ等"]:
                _add_trans(expense_value, c_transportation, pm_default)
            elif col2_val == "物販":
                _add_trans(expense_value, c_food, pm_default)
            elif col2_val == "ｵｰﾄ":
                amount_abs = abs(expense_value)
                pm_auto = Pmethod.objects.get(pk=14)
                _add_trans(amount_abs, c_move, pm_auto)
                _add_trans(-amount_abs, c_move, pm_default)
            else:
                _add_trans(expense_value, c_transportation, pm_default)

        context = {
            'pmethodgroup_list': pmethodgroup_list,
            'categorygroup_list': categorygroup_list,
            'category_list': category_list_all,
            'trans_list': trans_list,
        }
        return render(request, 'trans/suica_check.html', context)


def suica_check(request):
    suica_jaccs_register(request)

    return redirect('/t/')


def suica_jaccs_register(request):
    # checked trans
    tids = request.POST.getlist('tids')
    dates = request.POST.getlist('dates')
    cs = request.POST.getlist('cs')
    names = request.POST.getlist('names')
    expenses = request.POST.getlist('expenses')
    pmethods = request.POST.getlist('pmethods')
    memos = request.POST.getlist('memos')
    share_types = request.POST.getlist('share_types')

    i = 1
    for expense in expenses:
        if str(i) in tids:
            date = datetime.datetime.strptime(dates[i-1], '%Y/%m/%d')
            c = Category.objects.get(pk=cs[i-1])
            pm = Pmethod.objects.get(pk=pmethods[i-1])

            trans = Trans(date=date,
                          name=names[i-1],
                          expense=expenses[i-1],
                          memo=memos[i-1],
                          category=c,
                          pmethod=pm,
                          user=request.user,
                          share_type=share_types[i-1],
                          )
            trans.save()

        i += 1
    update_balance(trans)


# --- jaccs ----

def jaccs_upload(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        category_list.extend(clist)

    if request.method == 'GET':
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   }
        return render(request, 'trans/jaccs_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {'categorygroup_list': categorygroup_list,
                       'category_list': category_list,
                       'error_message': 'File is mandatory.',
                       }
            return render(request, 'trans/jaccs_upload.html', context)

        content = _read_uploaded_text(request.FILES['file'])

        fout = open('tmp_jaccs.txt', 'w')
        fout.write(content)
        fout.close()

        f = open('tmp_jaccs.txt', 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()

        # get default cate, pmethod
        cid = int(request.POST['c'])
        c = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=PM_JACCS_ID)

        keyword_category_mappings = _load_keyword_category_mapping(
            JACCS_CATEGORY_MAPPING_FNAME)
        category_cache = {}
        pmethod_cache = {}

        trans_list = []
        tmpid = 1
        for l in contents:
            splts = l.split('\t')

            if len(splts) == 1 or splts[1] == '':
                continue

            trans = TransUi()

            # this id is tmp
            trans.id = tmpid
            tmpid += 1
            date_part = splts[1].strip()
            if not date_part:
                continue
            m = re.search(r'(\d{2})/(\d{1,2})/(\d{1,2})', date_part)
            if not m:
                continue
            strdate = f"20{m.group(1)}/{m.group(2)}/{m.group(3)}"
            try:
                trans.date = datetime.datetime.strptime(strdate, '%Y/%m/%d')
            except ValueError:
                continue
            trans.name = (splts[2] + splts[3]).strip()

            expense = splts[10].replace(',', '')
            trans.expense = expense

            price = splts[8].replace(',', '')
            if expense != price:
                trans.memo = JACCS_DISCOUNT + price

            trans.category = _resolve_category_from_content(
                trans.name,
                c,
                keyword_category_mappings,
                category_cache,
            )
            trans.pmethod = pm

            trans.share_type = SHARE_TYPES_SHARE

            # check same trans--
            checktranslist = Trans.objects.filter(
                date=trans.date, expense=trans.expense, pmethod=pm)
            if len(checktranslist) > 0:
                trans.selected = False

            # tmp for migrated data
            datetmp = trans.date + timedelta(days=-1)
            checktranslist = Trans.objects.filter(date__gte=datetmp)\
                .filter(date__lte=trans.date)\
                .filter(expense=trans.expense, pmethod=pm)
            if len(checktranslist) > 0:
                trans.selected = False

            trans_list.append(trans)

        category_list = []
        if len(categorygroup_list) > 0:
            # find selected category group
            if 'cg' in request.POST:
                cg = CategoryGroup.objects.get(pk=int(request.POST['cg']))
            else:
                cg = categorygroup_list[0]
            clist = Category.objects.filter(group=cg).order_by('order')
            if 'c' in request.POST:
                for c in clist:
                    if c.id == int(request.POST['c']):
                        cui = CategoryUi()
                        cui.id = c.id
                        cui.name = c.name
                        cui.group = c.group
                        cui.selected = True
                        category_list.append(cui)
                    else:
                        category_list.append(c)
            else:
                category_list.extend(clist)

        # Ensure categories resolved via keyword mapping are selectable even if
        # they belong to a different group than the initially selected one.
        if len(trans_list) > 0:
            used_category_ids = {
                t.category.id for t in trans_list if getattr(t, 'category', None)}
            existing_category_ids = {c.id for c in category_list}
            missing_ids = used_category_ids - existing_category_ids
            if missing_ids:
                missing_categories = Category.objects.filter(
                    id__in=missing_ids).order_by('group__order', 'order')
                category_list.extend(list(missing_categories))

        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'trans_list': trans_list,
                   }
        return render(request, 'trans/jaccs_check.html', context)


def jaccs_check(request):
    suica_jaccs_register(request)

    return redirect('/t/')


def jaccs_upload_new(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        category_list.extend(clist)

    if request.method == 'GET':
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   }
        return render(request, 'trans/jaccs_upload_new.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {'categorygroup_list': categorygroup_list,
                       'category_list': category_list,
                       'error_message': 'File is mandatory.',
                       }
            return render(request, 'trans/jaccs_upload_new.html', context)

        content = _read_uploaded_text(request.FILES['file'])
        logger.info('[jaccs] new upload received: %s bytes',
                    len(content.encode('utf-8', errors='ignore')))

        tmp_fname = 'tmp_jaccs_new.txt'
        fout = open(tmp_fname, 'w')
        fout.write(content)
        fout.close()

        f = open(tmp_fname, 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()

        # get default cate, pmethod
        cid = int(request.POST['c'])
        c_default = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=PM_JACCS_ID)

        keyword_category_mappings = _load_keyword_category_mapping(
            JACCS_CATEGORY_MAPPING_FNAME)
        logger.info('[jaccs] keyword mappings loaded: %d entries',
                    len(keyword_category_mappings))
        category_cache = {}

        trans_list = []
        tmpid = 1
        data_started = False
        for l in contents:
            row = l.strip()

            if not data_started:
                if row.startswith('ご利用年月日'):
                    data_started = True
                continue

            if not row:
                continue

            if not re.match(r'^\d{4}/\d{1,2}/\d{1,2}', row):
                continue

            splts = [s.strip() for s in row.split(',')]
            if len(splts) < 7:
                logger.info('[jaccs] skip short row: %s', row)
                continue
            trans = TransUi()
            trans.id = tmpid
            tmpid += 1

            try:
                parsed_date = datetime.datetime.strptime(
                    splts[0], '%Y/%m/%d')
                trans.date = _make_aware(parsed_date)
            except ValueError:
                logger.info('[jaccs] skip row with invalid date: %s', splts[0])
                continue

            trans.name = splts[1]
            category_hint = splts[-1] if len(splts) > 0 else ''
            match_text = f"{trans.name} {category_hint}"

            price_raw = splts[6] if len(splts) > 6 else ''
            expense_raw = splts[8] if len(splts) > 8 else price_raw
            price = _clean_amount(price_raw)
            expense = _clean_amount(expense_raw)

            if expense == '':
                logger.info('[jaccs] skip row without expense: %s', row)
                continue

            trans.expense = expense

            if price and expense and expense != price:
                trans.memo = JACCS_DISCOUNT + price

            trans.category = _resolve_category_from_content(
                match_text,
                c_default,
                keyword_category_mappings,
                category_cache,
            )
            logger.warning(
                '[jaccs] resolved category %s (default %s) for "%s"',
                trans.category.id if trans.category else None,
                c_default.id if c_default else None,
                match_text)
            trans.pmethod = pm

            trans.share_type = SHARE_TYPES_SHARE

            # check same trans--
            checktranslist = Trans.objects.filter(
                date=trans.date, expense=trans.expense, pmethod=pm)
            if len(checktranslist) > 0:
                trans.selected = False

            trans_list.append(trans)

        category_list = []
        if len(categorygroup_list) > 0:
            # find selected category group
            if 'cg' in request.POST:
                cg = CategoryGroup.objects.get(pk=int(request.POST['cg']))
            else:
                cg = categorygroup_list[0]
            clist = Category.objects.filter(group=cg).order_by('order')
            if 'c' in request.POST:
                for c in clist:
                    if c.id == int(request.POST['c']):
                        cui = CategoryUi()
                        cui.id = c.id
                        cui.name = c.name
                        cui.group = c.group
                        cui.selected = True
                        category_list.append(cui)
                    else:
                        category_list.append(c)
            else:
                category_list.extend(clist)

        if len(trans_list) > 0:
            used_category_ids = {
                t.category.id for t in trans_list if getattr(t, 'category', None)}
            existing_category_ids = {c.id for c in category_list}
            missing_ids = used_category_ids - existing_category_ids
            if missing_ids:
                missing_categories = Category.objects.filter(
                    id__in=missing_ids).order_by('group__order', 'order')
                category_list.extend(list(missing_categories))

        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'trans_list': trans_list,
                   }
        return render(request, 'trans/jaccs_check.html', context)


# --- rakutencard ----

def rakutencard_upload(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        category_list.extend(clist)

    if request.method == 'GET':
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   }
        return render(request, 'trans/rakutencard_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {'categorygroup_list': categorygroup_list,
                       'category_list': category_list,
                       'error_message': 'File is mandatory.',
                       }
            return render(request, 'trans/rakutencard_upload.html', context)

        f = codecs.EncodedFile(request.FILES['file'], "utf-8")
        content = f.read()

        fout = open('tmp_rakutencard.txt', 'w')
        fout.write(content.decode('utf-8'))
        fout.close()

        f = open('tmp_rakutencard.txt', 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()

        # get default cate, pmethod
        cid = int(request.POST['c'])
        c = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=PM_RAKUTENCARD_ID)

        trans_list = []
        tmpid = 1
        for l in contents:
            splts = l.split(' ')

            if len(splts) == 1:
                continue

            trans = TransUi()

            # this id is tmp
            trans.id = tmpid
            tmpid += 1
            strdate = splts[0]
            trans.date = datetime.datetime.strptime(strdate, '%Y/%m/%d')
            trans.name = splts[1]

            expense = splts[4].replace(',', '')
            trans.expense = expense

            trans.category = c
            trans.pmethod = pm

            trans.share_type = SHARE_TYPES_SHARE

            # check same trans--
            checktranslist = Trans.objects.filter(
                date=trans.date, expense=trans.expense, pmethod=pm)
            if len(checktranslist) > 0:
                trans.selected = False

            trans_list.append(trans)

        category_list = []
        if len(categorygroup_list) > 0:
            # find selected category group
            if 'cg' in request.POST:
                cg = CategoryGroup.objects.get(pk=int(request.POST['cg']))
            else:
                cg = categorygroup_list[0]
            clist = Category.objects.filter(group=cg).order_by('order')
            if 'c' in request.POST:
                for c in clist:
                    if c.id == int(request.POST['c']):
                        cui = CategoryUi()
                        cui.id = c.id
                        cui.name = c.name
                        cui.group = c.group
                        cui.selected = True
                        category_list.append(cui)
                    else:
                        category_list.append(c)
            else:
                category_list.extend(clist)

        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'trans_list': trans_list,
                   }
        return render(request, 'trans/rakutencard_check.html', context)


def rakutencard_check(request):
    suica_rakutencard_register(request)

    return redirect('/t/')


def suica_rakutencard_register(request):
    # checked trans
    tids = request.POST.getlist('tids')
    dates = request.POST.getlist('dates')
    cs = request.POST.getlist('cs')
    names = request.POST.getlist('names')
    expenses = request.POST.getlist('expenses')
    pmethods = request.POST.getlist('pmethods')
    memos = request.POST.getlist('memos')
    share_types = request.POST.getlist('share_types')

    i = 1
    for expense in expenses:
        if str(i) in tids:
            date = datetime.datetime.strptime(dates[i-1], '%Y/%m/%d')
            c = Category.objects.get(pk=cs[i-1])
            pm = Pmethod.objects.get(pk=pmethods[i-1])

            trans = Trans(date=date,
                          name=names[i-1],
                          expense=expenses[i-1],
                          memo=memos[i-1],
                          category=c,
                          pmethod=pm,
                          user=request.user,
                          share_type=share_types[i-1],
                          )
            trans.save()

        i += 1
    update_balance(trans)


# --- shinsei ----

def shinsei_upload(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        category_list.extend(clist)

    date = datetime.datetime.now()
    year = date.year

    if request.method == 'GET':
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'year': year,
                   }
        return render(request, 'trans/shinsei_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {'categorygroup_list': categorygroup_list,
                       'category_list': category_list,
                       'year': year,
                       'error_message': 'File is mandatory.',
                       }
            return render(request, 'trans/shinsei_upload.html', context)

        content = _read_uploaded_text(request.FILES['file'])

        tmp_fname = 'tmp_shinsei.txt'
        with open(tmp_fname, 'w') as fout:
            fout.write(content)

        contents = content.splitlines()

        # get default cate, pmethod
        cid = int(request.POST['c'])
        c_default = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=PM_SHINSEI_ID)

        shinsei_mappings = _load_shinsei_mappings(
            SHINSEI_CATEGORY_MAPPING_FNAME)
        category_cache = {}
        pmethod_cache = {}

        year = request.POST['year']

        trans_list = []
        tmpid = 1
        for l in contents:
            row = l.strip()
            if not row:
                continue

            # expected format:
            # mm/dd [desc ...] expense income balance memo
            m = re.match(
                r'^\s*(\d{1,2}/\d{1,2})\s+(.*?)\s+([\d,]+)(?:\s+([\d,]+))?\s+([\d,]+)(?:\s+(.*))?$',
                row)
            if not m:
                continue

            date_part = m.group(1)
            strdate = f"{year}/{date_part}"

            try:
                parsed_date = datetime.datetime.strptime(strdate, '%Y/%m/%d')
            except ValueError:
                continue

            expense_raw = m.group(3)
            income_raw = m.group(4)
            balance_raw = m.group(5)

            expense_val = _clean_amount(expense_raw)
            income_val = _clean_amount(income_raw)

            if expense_val == '' and income_val == '':
                continue

            # keep base amount from source columns for move splits
            base_amount_raw = expense_val if expense_val != '' else income_val
            base_amount = int(base_amount_raw) if base_amount_raw else 0

            # Expense column is outflow; income column is inflow.
            if income_val:
                amount = -int(income_val)
            elif expense_val.startswith('-'):
                amount = int(expense_val)
            else:
                inflow_hints = ('振込', '振替', '給与', '賞与', '利息')
                amount = -int(expense_val) if any(h in m.group(2) for h in inflow_hints) else int(expense_val)

            desc = (m.group(2) or '').strip()
            detail_text = (m.group(6) or '').strip()
            name_parts = [p for p in (desc, detail_text) if p]
            display_name = ' '.join(name_parts) if name_parts else desc

            # category is determined primarily from the last column, but include
            # description to widen the hit surface for mappings.
            match_text = ' '.join([t for t in (detail_text, desc) if t])
            mapping = _match_shinsei_mapping(match_text, shinsei_mappings)

            def _get_category(cid):
                if cid is None:
                    return None
                if cid in category_cache:
                    return category_cache[cid]
                try:
                    category_cache[cid] = Category.objects.get(pk=cid)
                    return category_cache[cid]
                except Category.DoesNotExist:
                    return None

            def _get_pmethod(pid):
                if pid is None:
                    return None
                if pid in pmethod_cache:
                    return pmethod_cache[pid]
                try:
                    pmethod_cache[pid] = Pmethod.objects.get(pk=pid)
                    return pmethod_cache[pid]
                except Pmethod.DoesNotExist:
                    return None

            def _add_trans(expense_value, category_obj, pmethod_obj):
                nonlocal tmpid
                trans = TransUi()
                trans.id = tmpid
                tmpid += 1
                trans.date = _make_aware(parsed_date)
                trans.name = display_name
                trans.expense = expense_value
                trans.category = category_obj or c_default
                trans.pmethod = pmethod_obj or pm
                trans.share_type = SHARE_TYPES_SHARE
                # check duplicates
                checktranslist = Trans.objects.filter(
                    date=trans.date, expense=trans.expense, user=request.user)
                if len(checktranslist) > 0:
                    trans.selected = False
                trans_list.append(trans)

            if mapping and mapping.get('move_type') in ('move-to', 'move-from') and mapping.get('move_category_id'):
                amount_abs = abs(base_amount)
                move_cat = _get_category(mapping.get('move_category_id'))
                move_default_cat = _get_category(C_MOVE_ID)
                if move_default_cat is None:
                    move_default_cat = Category.objects.filter(
                        name__icontains='move').order_by('id').first() or Category.objects.filter(name__icontains='移動').order_by('id').first()
                move_method = _get_pmethod(mapping.get('move_method_id'))
                move_default_method = _get_pmethod(PM_SHINSEI_ID)

                if mapping['move_type'] == 'move-to':
                    # outflow to move (pm 13), inflow to target (pm from mapping) both as move category
                    _add_trans(amount_abs, move_default_cat, move_default_method)
                    _add_trans(-amount_abs, move_default_cat, move_method)
                else:
                    # outflow from target (pm from mapping), inflow to move (pm 13)
                    _add_trans(amount_abs, move_default_cat, move_method)
                    _add_trans(-amount_abs, move_default_cat, move_default_method)
            else:
                target_category = _get_category(mapping['category_id']) if mapping else c_default
                _add_trans(amount, target_category, pm)

        category_list = []
        if len(categorygroup_list) > 0:
            # find selected category group
            if 'cg' in request.POST:
                cg = CategoryGroup.objects.get(pk=int(request.POST['cg']))
            else:
                cg = categorygroup_list[0]
            clist = Category.objects.filter(group=cg).order_by('order')
            if 'c' in request.POST:
                for c in clist:
                    if c.id == int(request.POST['c']):
                        cui = CategoryUi()
                        cui.id = c.id
                        cui.name = c.name
                        cui.group = c.group
                        cui.selected = True
                        category_list.append(cui)
                    else:
                        category_list.append(c)
            else:
                category_list.extend(clist)

        if len(trans_list) > 0:
            used_category_ids = {
                t.category.id for t in trans_list if getattr(t, 'category', None)}
            existing_category_ids = {c.id for c in category_list}
            missing_ids = used_category_ids - existing_category_ids
            if missing_ids:
                missing_categories = Category.objects.filter(
                    id__in=missing_ids).order_by('group__order', 'order')
                category_list.extend(list(missing_categories))

        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'trans_list': trans_list,
                   }
        return render(request, 'trans/shinsei_check.html', context)


def shinsei_check(request):
    suica_shinsei_register(request)

    return redirect('/t/')


def suica_shinsei_register(request):
    # checked trans
    tids = request.POST.getlist('tids')
    dates = request.POST.getlist('dates')
    cs = request.POST.getlist('cs')
    names = request.POST.getlist('names')
    expenses = request.POST.getlist('expenses')
    pmethods = request.POST.getlist('pmethods')
    memos = request.POST.getlist('memos')
    share_types = request.POST.getlist('share_types')

    i = 1
    for expense in expenses:
        if str(i) in tids:
            date = datetime.datetime.strptime(dates[i-1], '%Y/%m/%d')
            c = Category.objects.get(pk=cs[i-1])
            pm = Pmethod.objects.get(pk=pmethods[i-1])

            trans = Trans(date=date,
                          name=names[i-1],
                          expense=expenses[i-1],
                          memo=memos[i-1],
                          category=c,
                          pmethod=pm,
                          user=request.user,
                          share_type=share_types[i-1],
                          )
            trans.save()

        i += 1
    update_balance(trans)


# --- generic CSV upload (simple format) ----

def csv_upload(request):
    """
    Upload CSV with format:
    取引日(YYYYMMDD),入出金(円),取引後残高(円),入出金内容
    """
    categorygroup_list = CategoryGroup.objects.order_by('order')

    pmethodgroup_list = PmethodGroup.objects.filter(
        user=request.user).order_by('order')
    selected_pmg_id = None
    selected_pm_id = PM_RAKUTENBANK_ID
    pmethod_list = []
    if len(pmethodgroup_list) > 0:
        if 'pmg' in request.POST:
            selected_pmg_id = int(request.POST['pmg'])
            pmg = PmethodGroup.objects.get(pk=selected_pmg_id)
        else:
            pmg = pmethodgroup_list[0]
            selected_pmg_id = pmg.id
        pmethod_list = list(Pmethod.objects.filter(
            group=pmg).order_by('order'))
        if 'pm' in request.POST:
            selected_pm_id = int(request.POST['pm'])
        else:
            # default to Rakuten bank id when available
            if not any(pm.id == PM_RAKUTENBANK_ID for pm in pmethod_list):
                selected_pm_id = pmethod_list[0].id
    else:
        pmethod_list = []

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        category_list.extend(clist)

    if request.method == 'GET':
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'pmethodgroup_list': pmethodgroup_list,
                   'pmethod_list': pmethod_list,
                   'selected_pmg_id': selected_pmg_id,
                   'selected_pm_id': selected_pm_id}
        return render(request, 'trans/csv_upload.html', context)

    if not request.FILES.get('file'):
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'pmethodgroup_list': pmethodgroup_list,
                   'pmethod_list': pmethod_list,
                   'selected_pmg_id': selected_pmg_id,
                   'selected_pm_id': selected_pm_id,
                   'error_message': 'File is mandatory.'}
        return render(request, 'trans/csv_upload.html', context)

    content = _read_uploaded_text(request.FILES['file'])
    lines = content.splitlines()

    # default category, pmethod
    cid = int(request.POST['c'])
    c_default = Category.objects.get(pk=cid)
    pmid = request.POST.get('pm')
    try:
        pm = Pmethod.objects.get(pk=pmid)
    except (Pmethod.DoesNotExist, ValueError, TypeError):
        pm = Pmethod.objects.filter(pk=PM_RAKUTENBANK_ID).first()
        if pm is None and pmethod_list:
            pm = pmethod_list[0]

    trans_list = []
    tmpid = 1
    for row in lines:
        if not row or '取引日' in row:
            continue

        cols = [col.strip() for col in row.split(',')]
        if len(cols) < 4:
            continue

        date_raw = cols[0]
        try:
            parsed_date = datetime.datetime.strptime(date_raw, '%Y%m%d')
            parsed_date = _make_aware(parsed_date)
        except ValueError:
            continue

        amount_raw = _clean_amount(cols[1])
        if amount_raw == '':
            continue

        amt = int(amount_raw)
        # Positive amounts are income (store as negative); negatives are expense.
        expense_val = -amt if amt > 0 else abs(amt)

        name = cols[3]

        trans = TransUi()
        trans.id = tmpid
        tmpid += 1
        trans.date = parsed_date
        trans.name = name
        trans.expense = expense_val
        trans.category = c_default
        trans.pmethod = pm
        trans.share_type = SHARE_TYPES_SHARE
        trans.memo = ''

        checktranslist = Trans.objects.filter(
            date=trans.date, expense=trans.expense, user=request.user)
        if len(checktranslist) > 0:
            trans.selected = False
        trans_list.append(trans)

    # rebuild category list with selection retained
    category_list = []
    if len(categorygroup_list) > 0:
        if 'cg' in request.POST:
            cg = CategoryGroup.objects.get(pk=int(request.POST['cg']))
        else:
            cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        if 'c' in request.POST:
            for c in clist:
                if c.id == int(request.POST['c']):
                    cui = CategoryUi()
                    cui.id = c.id
                    cui.name = c.name
                    cui.group = c.group
                    cui.selected = True
                    category_list.append(cui)
                else:
                    category_list.append(c)
        else:
            category_list.extend(clist)

    context = {'categorygroup_list': categorygroup_list,
               'category_list': category_list,
               'trans_list': trans_list}
    return render(request, 'trans/csv_check.html', context)


def csv_check(request):
    suica_shinsei_register(request)
    return redirect('/t/')


def paypay_upload(request):
    """Upload PayPay card CSV and map categories by keyword (like JACCS)."""
    categorygroup_list = CategoryGroup.objects.order_by('order')

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        category_list.extend(clist)

    if request.method == 'GET':
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   }
        return render(request, 'trans/paypay_upload.html', context)

    if not request.FILES.get('file'):
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'error_message': 'File is mandatory.',
                   }
        return render(request, 'trans/paypay_upload.html', context)

    content = _read_uploaded_text(request.FILES['file'])

    # get default cate, pmethod
    cid = int(request.POST['c'])
    c_default = Category.objects.get(pk=cid)
    pm = Pmethod.objects.get(pk=PM_PAYPAYCARD_ID)

    keyword_category_mappings = _load_keyword_category_mapping(
        PAYPAY_CATEGORY_MAPPING_FNAME)
    category_cache = {}

    trans_list = []
    tmpid = 1

    reader = csv.reader(io.StringIO(content))
    for row in reader:
        if not row:
            continue
        if row[0].startswith('利用日'):
            continue
        if len(row) < 6:
            continue

        try:
            parsed_date = datetime.datetime.strptime(row[0].strip(), '%Y/%m/%d')
            date = _make_aware(parsed_date)
        except ValueError:
            continue

        name = row[1].strip()
        expense_raw = _clean_amount(row[5])
        if expense_raw == '':
            continue
        expense_val = int(expense_raw)

        trans = TransUi()
        trans.id = tmpid
        tmpid += 1
        trans.date = date
        trans.name = name
        trans.expense = expense_val

        match_text = name
        trans.category = _resolve_category_from_content(
            match_text,
            c_default,
            keyword_category_mappings,
            category_cache,
        ) or c_default
        trans.pmethod = pm
        trans.share_type = SHARE_TYPES_SHARE
        trans.memo = ''

        checktranslist = Trans.objects.filter(
            date=trans.date, expense=trans.expense, pmethod=pm)
        if len(checktranslist) > 0:
            trans.selected = False

        trans_list.append(trans)

    category_list = []
    if len(categorygroup_list) > 0:
        # find selected category group
        if 'cg' in request.POST:
            cg = CategoryGroup.objects.get(pk=int(request.POST['cg']))
        else:
            cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        if 'c' in request.POST:
            for c in clist:
                if c.id == int(request.POST['c']):
                    cui = CategoryUi()
                    cui.id = c.id
                    cui.name = c.name
                    cui.group = c.group
                    cui.selected = True
                    category_list.append(cui)
                else:
                    category_list.append(c)
        else:
            category_list.extend(clist)

    if len(trans_list) > 0:
        used_category_ids = {
            t.category.id for t in trans_list if getattr(t, 'category', None)}
        existing_category_ids = {c.id for c in category_list}
        missing_ids = used_category_ids - existing_category_ids
        if missing_ids:
            missing_categories = Category.objects.filter(
                id__in=missing_ids).order_by('group__order', 'order')
            category_list.extend(list(missing_categories))

    context = {'categorygroup_list': categorygroup_list,
               'category_list': category_list,
               'trans_list': trans_list,
               }
    return render(request, 'trans/paypay_check.html', context)


def paypay_check(request):
    suica_jaccs_register(request)
    return redirect('/t/')


# --- salary ----

def salary_upload(request):
    pmethodgroup_list = PmethodGroup.objects.filter(
        user=request.user).order_by('order')

    pmethod_list = []
    if len(pmethodgroup_list) > 0:
        pmg = pmethodgroup_list[0]
        pmlist = Pmethod.objects.filter(group=pmg).order_by('order')
        pmethod_list.extend(pmlist)

    if request.method == 'GET':
        context = {'pmethodgroup_list': pmethodgroup_list,
                   'pmethod_list': pmethod_list,
                   }
        return render(request, 'trans/salary_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {
                'pmethodgroup_list': pmethodgroup_list,
                'pmethod_list': pmethod_list,
                'error_message': 'File is mandatory.',
            }
            return render(request, 'trans/salary_upload.html', context)

        if request.POST['date'] == '':
            context = {
                'pmethodgroup_list': pmethodgroup_list,
                'pmethod_list': pmethod_list,
                'error_message': 'Date should be YY/mm/dd.' + request.POST['date'],
            }
            return render(request, 'trans/salary_upload.html', context)

        f = request.FILES['file']

        with open('tmp_salary.txt', 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)

        f = open('tmp_salary.txt', 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()

        # open mapping between item and cid--
        f = open(SALARY_MAPPING_FNAME, 'r')
        CS_SALARY = {}
        for l in f.readlines():
            splts = l.split(',')
            CS_SALARY[splts[0]] = int(splts[1])
        f.close()

        # get default pmethod
        pmid = int(request.POST['pm'])
        pm = Pmethod.objects.get(pk=pmid)

        trans_list = []
        tmpid = 1
        fIncome = True
        for l in contents:
            if 'in\n' == l:
                fIncome = True
                continue
            elif 'out\n' == l:
                fIncome = False
                continue

            splts = l.split(' : ')
            trans = TransUi()

            # this id is tmp
            trans.id = tmpid
            tmpid += 1
            strdate = request.POST['date']
            trans.date = datetime.datetime.strptime(strdate, '%Y/%m/%d')

            trans.name = ''
            expense = splts[1].replace(',', '').replace('\n', '')
            expense = expense.replace('−', '-')
            if fIncome:
                if not expense.count('-'):
                    expense = '-' + expense
                else:
                    expense = expense.replace('-', '')

            trans.expense = expense
            trans.pmethod = pm

            trans.name = splts[0]

            # category
            if not splts[0] in CS_SALARY:
                cid = SALARY_OTHER_ID
            else:
                cid = CS_SALARY[splts[0]]
            c = Category.objects.get(pk=cid)
            trans.category = c

            # check same trans
            checktranslist = Trans.objects.filter(
                date=trans.date, expense=trans.expense, category=c, pmethod=pm)

            if len(checktranslist) > 0:
                trans.selected = False

            trans_list.append(trans)

        context = {
            'trans_list': trans_list,
        }
        return render(request, 'trans/salary_check.html', context)


def salary_check(request):
    suica_jaccs_register(request)

    return redirect('/t/')

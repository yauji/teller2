import datetime
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
    SUICA_KURIKOSHI,
    JACCS_DISCOUNT,
    CATEGORY_ID_TRANSPORTATION,
    PM_JACCS_ID,
    PM_RAKUTENCARD_ID,
    PM_SHINSEI_ID,
    SALARY_MAPPING_FNAME,
    JACCS_CATEGORY_MAPPING_FNAME,
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


# --- suica ----

def suica_upload(request):
    categorygroup_list = CategoryGroup.objects.order_by('order')

    category_list = []
    if len(categorygroup_list) > 0:
        cg = categorygroup_list[0]
        clist = Category.objects.filter(group=cg).order_by('order')
        category_list.extend(clist)

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
        context = {'categorygroup_list': categorygroup_list,
                   'category_list': category_list,
                   'pmethodgroup_list': pmethodgroup_list,
                   'pmethod_list': pmethod_list,
                   'year': year,
                   }
        return render(request, 'trans/suica_upload.html', context)

    elif request.method == 'POST':
        if not 'file' in request.FILES:
            context = {'categorygroup_list': categorygroup_list,
                       'category_list': category_list,
                       'pmethodgroup_list': pmethodgroup_list,
                       'pmethod_list': pmethod_list,
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

        # get default cate, pmethod
        cid = int(request.POST['c'])
        pmid = int(request.POST['pm'])
        c = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=pmid)

        c_transportation = Category.objects.get(pk=CATEGORY_ID_TRANSPORTATION)

        trans_list = []
        tmpid = 1
        for l in contents:
            if len(l.strip()) == 0:
                continue

            splts = l.split('\t')
            # Drop empty columns while keeping order for newer formats.
            parts = [p for p in splts if p.strip() != '']

            trans = TransUi()
            # trans = Trans()

            # this id is tmp
            trans.id = tmpid
            tmpid += 1

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
            trans.date = datetime.datetime.strptime(strdate, '%Y/%m/%d')

            # --- name ---
            if len(splts) >= 6:
                name_parts = splts[2:6]
            elif len(parts) > 1:
                # Newer format: type/from/to are in the middle, amounts at the end
                name_parts = parts[1:-2] if len(parts) > 3 else parts[1:]
            else:
                name_parts = []
            trans.name = ''.join(name_parts).strip()

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
                trans.expense = int(expense) * -1
            else:
                continue

            str0 = ''
            if len(splts) >= 3:
                str0 = splts[2].strip()
            elif len(parts) >= 2:
                str0 = parts[1].strip()

            if str0 in ["入", "ﾊﾞｽ等"]:
                trans.category = c_transportation
            else:
                trans.category = c

            trans.pmethod = pm

            # check same trans
            checktranslist = Trans.objects.filter(
                date=trans.date, expense=trans.expense, category=trans.category, pmethod=pm)

            if len(checktranslist) > 0:
                trans.selected = False

            # チャージの場合、（「ｵｰﾄ」から始まる場合）、チェックを外す
            if str0 == "ｵｰﾄ":
                trans.selected = False

            if trans.name != SUICA_KURIKOSHI:
                trans_list.append(trans)

        context = {'categorygroup_list': categorygroup_list,
                   'pmethodgroup_list': pmethodgroup_list,
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

        f = codecs.EncodedFile(request.FILES['file'], "utf-8")
        content = f.read()

        fout = open('tmp_shinsei.txt', 'w')
        fout.write(content.decode('utf-8'))
        fout.close()

        f = open('tmp_shinsei.txt', 'r')
        contents = []
        for l in f.readlines():
            contents.append(l)
        f.close()

        # get default cate, pmethod
        cid = int(request.POST['c'])
        c = Category.objects.get(pk=cid)
        pm = Pmethod.objects.get(pk=PM_SHINSEI_ID)
        
        year = request.POST['year']

        trans_list = []
        tmpid = 1
        for l in contents:
            splts = l.split(' ')

            if len(splts) != 5:
                continue

            trans = TransUi()

            # this id is tmp
            trans.id = tmpid
            tmpid += 1
            strdate = year + '/' + splts[0]
            trans.date = datetime.datetime.strptime(strdate, '%Y/%m/%d')
            trans.name = splts[4]

            expense = splts[2].replace(',', '')
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

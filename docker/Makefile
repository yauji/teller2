IMAGE=teller2
VERSION=0.1

build:
	-mkdir code
	cp -r ../teller2 code
	cp -r ../trans code
	cp -r ../manage.py code
	cp -r ../templates code
	cp -r ../static code
	tar czvf code.tar.gz code
	docker build -t $(IMAGE):$(VERSION) .


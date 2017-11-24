NAME=teller2
VERSION=0.1

build:
	-mkdir teller2
	cp -r ../teller2 teller2
	cp -r ../trans teller2
	cp -r ../manage.py teller2
	cp -r ../templates teller2
	cp -r ../static teller2
	tar czvf teller2.tar.gz teller2
	docker build -t $(NAME):$(VERSION) .

start:
	docker run -itd \
		-p 8000:8000 \
	        --name $(NAME) \
	        $(NAME):$(VERSION)

contener=`docker ps -a -q`
image=`docker images | awk '/^<none>/ { print $$3 }'`

clean:
	@if [ "$(image)" != "" ] ; then \
		docker rmi $(image); \
	fi
	@if [ "$(contener)" != "" ] ; then \
		docker rm $(contener); \
	fi

stop:
	docker rm -f $(NAME)

shell:
	docker exec -it $(NAME) /bin/bash

#NAME=teller2
NAME=docker-web-1
VERSION=0.1

build:
	-rm -rf teller2
	-rm teller2.tar.gz
	-mkdir teller2
	cp -r ../teller2 teller2
	cp -r ../trans teller2
	cp -r ../manage.py teller2
	cp -r ../templates teller2
	cp -r ../static teller2
	cp -r ../mapping_item_cid.txt teller2
	tar czvf teller2.tar.gz teller2
	docker-compose build
	#docker build -t $(NAME):$(VERSION)  .

start:
	docker run -it \
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

up: build
	docker-compose up -d

down:
	docker-compose down

shell:
	docker exec -it $(NAME) /bin/bash

build-dev:
	docker-compose -f docker-compose.dev.yml build

up-dev: build-dev
	docker-compose -f docker-compose.dev.yml up -d

down-dev:
	docker-compose -f docker-compose.dev.yml down

shell-dev:
	docker exec -it $(NAME) /bin/bash
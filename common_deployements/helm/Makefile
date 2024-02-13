.ONESHELL:
SHELL=/bin/bash
build:
	@cd dummy
	rev=$$(cat .revision)
	expr $$rev + 1 > .revision
	image_with_tag=$${IMAGE_URL:-hexbioc/dummy-celery}:$$(cat .revision)
	docker build -t "$$image_with_tag" .
	docker push "$$image_with_tag"
	printf "Pushed container with revision $$(cat .revision)!\n"


install:
	@helm install $${HELM_NAME:-ch} celery-helm


upgrade:
	@helm upgrade $${HELM_NAME:-ch} celery-helm

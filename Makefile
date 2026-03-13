TARBALL := $(shell python setup.py --name)-$(shell python setup.py --version).tar.gz

dist/$(TARBALL):
	python setup.py sdist

$(TARBALL): dist/$(TARBALL)
	cp dist/$(TARBALL) .

clean:
	rm -rf noarch/ BUILDROOT/
	rm -f *.tar.gz

distclean: clean
	rm -f *.rpm
	rm -rf dist/

rpm: $(TARBALL)
	rpmbuild --define "_topdir %(pwd)" \
	--define "_builddir /tmp" \
	--define "_rpmdir %{_topdir}" \
	--define "_srcrpmdir %{_topdir}" \
	--define "_specdir %{_topdir}" \
	--define "_sourcedir %{_topdir}" \
	-ba django-ses.spec

	mv noarch/*.rpm .

rpm-test:
	rpmlint -i *.rpm *.spec

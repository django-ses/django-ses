%{!?python_sitelib: %define python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")}
%{!?pyver: %define pyver %(%{__python} -c "import sys ; print sys.version[:3]")}

Name:           %(%{__python} setup.py --name)
Version:        %(%{__python} setup.py --version)
Release:        1%{?dist}
Summary:        %(%{__python} setup.py --description)

Group:          Development/Libraries
License:        %(%{__python} setup.py --license)
URL:            %(%{__python} setup.py --url)
Source0:        http://pypi.python.org/packages/source/d/django-ses/%{name}-%{version}.tar.gz

BuildRoot:      %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildArch:      noarch
BuildRequires:  python-devel

# NB: update this when updating setup.py
Requires:       Django
Requires:       python-boto >= 2.1.0


%description
%(%{__python} setup.py --description)

%prep
%setup -q

%build
%{__python} setup.py build

%install
rm -rf $RPM_BUILD_ROOT
%{__python} setup.py install --skip-build --root $RPM_BUILD_ROOT

mkdir -p %{buildroot}/%{_docdir}/%{name}-%{version}
install -m 0644 README.rst %{buildroot}/%{_docdir}/%{name}-%{version}
install -m 0644 LICENSE %{buildroot}/%{_docdir}/%{name}-%{version}
cp -r example/ %{buildroot}/%{_docdir}/%{name}-%{version}

%clean
rm -rf $RPM_BUILD_ROOT


%files
%defattr(-,root,root,-)
%doc %{_docdir}/%{name}-%{version}/LICENSE
%doc %{_docdir}/%{name}-%{version}/README.rst
%{_docdir}/%{name}-%{version}/example/*
%{python_sitelib}/django_ses/*

# Leaving these since people may want to rebuild on older dists
%if 0%{?fedora} >= 9 || 0%{?rhel} >= 6
    %{python_sitelib}/*.egg-info
%endif

%changelog

* Thu Jan 21 2016 Alexander Todorov <atodorov@MrSenko.com> - 0.7.0-1
- initial build

Summary: gNMI client
Name: gnmi-py
Version: 0.4.5
Release: 1%{?dist}
URL: https://github.com/arista-northwest/gnmi-py
Source: %{_name}-%{version}.tar.gz
License: MIT
BuildArch: noarch
Vendor: Jesse Mather <jmather@arista.com>

Requires: python%{python3_pkgversion}-grpcio


%description
gNMI client and cli.

%prep
%autosetup -p1 -n gnmipy-%{version}

%build
%pyproject_sdist
%pyproject_wheel

%install
%pyproject_install

%clean
rm -rf $RPM_BUILD_ROOT

%files -f INSTALLED_FILES

%defattr(-,root,root)
#!/bin/bash
#myInvocation="$(printf %q "$BASH_SOURCE")$((($#)) && printf ' %q' "$@")"
SUFFIX='-kali';
exec 3>&1 4>&2
trap 'exec 2>&4 1>&3' 0 1 2 3
exec 1>/tmp/setup-kali.out 2>&1
startup ()
{
	install_packages;
	stage_apache;
	change_hostname;
	exit;
}


install_packages ()
{
	touch ~/.hushlogin;
	touch /home/kali/.hushlogin;
	sudo apt-get -yqq update;
	sudo apt-get -yqq install jq net-tools;
}

stage_apache ()
{
	sudo service apache2 start;
	sudo wget -q 'http://provisioning.aws.cs-labs.net/workshop/cwp/collection.sh' -O /var/www/html/collection.sh;
	sudo wget -q 'http://provisioning.aws.cs-labs.net/workshop/cwp/defense_evasion.sh' -O /var/www/html/defense_evasion.sh;
	sudo wget -q 'http://provisioning.aws.cs-labs.net/workshop/cwp/exfiltration.sh' -O /var/www/html/exfiltration.sh;
	sudo wget -q 'http://provisioning.aws.cs-labs.net/workshop/cwp/mimipenguin.sh' -O /var/www/html/mimipenguin.sh;
}

change_hostname ()
{
	# shellcheck disable=SC2002
	ENV_HASH=$(cat /proc/sys/kernel/random/uuid | sed 's/[-]//g' | head -c 5; echo;);
	sudo hostnamectl set-hostname "${ENV_HASH}${SUFFIX}";
	sudo echo "127.0.0.1 ${ENV_HASH}${SUFFIX}" | sudo tee -a /etc/hosts
}


startup;

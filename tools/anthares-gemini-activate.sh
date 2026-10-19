#!/bin/bash
set -eu
cd /home/u566597497/domains/anthares.us/public_html
f='wp-config.php'
if grep -q 'ANTHARES_AI_EXTERNAL_SECRETS_PROVIDERS' "$f";then
  grep -q "'gemini'" "$f" || { echo EXTERNAL_PROVIDERS_CHANGED_ABORT; exit 12; }
  echo PRODUCTION_OPTIN_ALREADY_PRESENT
  exit 0
fi
d="$HOME/.anthares-backups/ai-hub"
mkdir -p "$d";chmod 700 "$d"
b="$d/wp-config-pre-bws-20261019.php"
if [ ! -e "$b" ];then cp -p "$f" "$b";chmod 600 "$b";fi
/opt/alt/php82/usr/bin/php /usr/local/bin/wp-cli-2.12.0.phar config set ANTHARES_AI_EXTERNAL_SECRETS_PROVIDERS "array('gemini')" --raw --type=constant --path="$PWD" >/dev/null
if ! /opt/alt/php82/usr/bin/php -l "$f" >/dev/null;then cp -p "$b" "$f";echo WP_CONFIG_LINT_ROLLBACK;exit 13;fi
home=$(curl -sSL -o /dev/null -w '%{http_code}' --max-time 12 https://anthares.us/)
rest=$(curl -sSL -o /dev/null -w '%{http_code}' --max-time 12 https://anthares.us/wp-json/)
if [ "$home" != 200 ] || [ "$rest" != 200 ];then cp -p "$b" "$f";echo WP_CONFIG_HEALTH_ROLLBACK;exit 14;fi
echo ANTHARES_WORDPRESS_GEMINI_OPTIN=PASS

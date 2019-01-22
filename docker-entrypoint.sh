#!/bin/bash
set -eo pipefail

# if command starts with an option, prepend web3-gear
if [ "${1:0:1}" = '-' ]; then
	set -- web3-gear "$@"
fi

# Check if LISTEN_HOST is not set
if [[ -z "${LISTEN_HOST}" ]]; then
  LISTEN_HOST="0.0.0.0"
else
  LISTEN_HOST="${LISTEN_HOST}"
fi

# Check if LISTEN_PORT is not set
if [[ -z "${LISTEN_PORT}" ]]; then
  LISTEN_PORT="8545"
else
  LISTEN_PORT="${LISTEN_PORT}"
fi

# Check if THOR_IP is not set
if [[ -z "${THOR_IP}" ]]; then
  echo "Env variable needed: eg. THOR_IP=127.0.0.1 or THOR_IP=www.example.com"
  exit 1
fi

# check if THOR_PORT is not set
if [[ -z "${THOR_PORT}" ]]; then
  echo "Env variable needed: eg. THOR_PORT=8669"
  exit 1
fi

# check if THOR_PROTOCOL is not set
if [[ -z "${THOR_PROTOCOL}" ]]; then
  THOR_PROTOCOL='http'
else
  THOR_PROTOCOL="${THOR_PROTOCOL}"
fi

echo "Using thor point: ${THOR_PROTOCOL}://${THOR_IP}:${THOR_PORT}"

LC_ALL="C.UTF-8" LANG="C.UTF-8" web3-gear --host ${LISTEN_HOST} --port ${LISTEN_PORT} --endpoint "${THOR_PROTOCOL}://${THOR_IP}:${THOR_PORT}"

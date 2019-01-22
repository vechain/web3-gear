FROM ubuntu:18.04

# Ports that should be exposed
EXPOSE 8545/tcp
EXPOSE 8545/udp

# Install web3-gear
USER root
RUN apt-get update
RUN apt-get install -qqy libssl-dev
RUN apt-get install -qqy python3-pip
RUN pip3 install web3-gear

# Test if command exist, installation complete.
RUN bash -c '[[ $(which web3-gear) == "/usr/local/bin/web3-gear" ]] || exit 1'

# Entry point
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod 777 /usr/local/bin/docker-entrypoint.sh

# Backwards compatibility
RUN ln -s usr/local/bin/docker-entrypoint.sh /entrypoint.sh

# See docker-entrypoint.sh for details
ENTRYPOINT ["docker-entrypoint.sh"]

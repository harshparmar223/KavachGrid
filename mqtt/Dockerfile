FROM eclipse-mosquitto:2

# Copy configuration files
COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY acl.conf /mosquitto/config/acl.conf
COPY passwd /mosquitto/config/passwd
COPY certs/ /mosquitto/certs/

# Create required directories
RUN mkdir -p /mosquitto/data /mosquitto/log /mosquitto/certs

# Expose ports
EXPOSE 1883 8883 9001

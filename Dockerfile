# Build stage
FROM qratehcc2sdk.azurecr.io/python:3.12-slim-2024-04-19-debugbuild AS builder-image  

WORKDIR /app

# Add App packages (needed to be done here becase this stage has pip) 
COPY requirements.txt .
COPY packages ./packages

# Add Python packages
RUN pip3 install -r requirements.txt && pip3 install typing-extensions --upgrade
RUN pip3 install packages/hcc2sdk-0.1.0-py3-none-any.whl

# Uninstall pip (pip is installed into /usr/local/lib/python3.12/site-packages/pip & is not needed on the target)
RUN pip3 uninstall -y pip

# Install packages needed by pip packages
RUN apt-get update && apt-get install -y zlib1g-dev libssl-dev

# Run stage
FROM qratehcc2sdk.azurecr.io/static-debian12:262ae336-distroless-py-2024-04-27-prod AS runner-image

# Determine chipset architecture for copying python
ARG CHIPSET_ARCH=x86_64-linux-gnu

# Copy python from builder
COPY --from=builder-image /usr/local/lib/ /usr/local/lib/
COPY --from=builder-image /usr/local/bin/python3.12 /usr/local/bin/python3.12
COPY --from=builder-image /etc/ld.so.cache /etc/ld.so.cache

# Copy pip's dependencies (this will could change, depending on pip package requirements)
COPY --from=builder-image /lib64/ld-linux-x86-64.so.2 /lib64/
COPY --from=builder-image /lib/${CHIPSET_ARCH}/libc.so.6 /lib/${CHIPSET_ARCH}/
COPY --from=builder-image /lib/${CHIPSET_ARCH}/libm.so.6 /lib/${CHIPSET_ARCH}/
COPY --from=builder-image /lib/${CHIPSET_ARCH}/libssl.so.3 /lib/${CHIPSET_ARCH}/libssl.so.3
COPY --from=builder-image /lib/${CHIPSET_ARCH}/libcrypto.so.3 /lib/${CHIPSET_ARCH}/libcrypto.so.3
COPY --from=builder-image /lib/${CHIPSET_ARCH}/libz.so.1 /lib/${CHIPSET_ARCH}/libz.so.1

# Copy installed Python packages from builder stage
COPY --from=builder-image /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Add App code and configuration
WORKDIR /app

COPY *.py .
COPY appconfig ./appconfig


# Run the App entrypoint module
CMD ["/usr/local/bin/python3.12", "main.py"]
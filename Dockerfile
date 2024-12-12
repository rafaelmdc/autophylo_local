FROM pegi3s/docker:20.04

# Update the system and install Python3, pip, and other dependencies
RUN apt-get update -y && \
    apt-get install -y unzip python3 python3-pip && \
    apt-get clean

# Install Python packages
RUN pip3 install --no-cache-dir biopython pandas matplotlib

WORKDIR /opt

# Copy necessary files

#Version of autophylo to run
COPY version3.zip /opt 

COPY /python_modules/ /opt/
COPY /driver_modules/ /opt/

# Unzip the file and remove the zip
RUN unzip version3.zip && \
    rm /opt/version3.zip

# Set permissions
RUN chmod 777 *

# Define the command to run your main script
CMD /opt/pre_main

FROM pegi3s/docker:20.04

# Update the system and install Python3, pip, and other dependencies
RUN apt-get update -y && \
    apt-get install -y unzip python3 python3-pip && \
    apt-get clean

# Install Python packages
RUN pip3 install --no-cache-dir biopython pandas matplotlib

WORKDIR /opt

# Copy necessary files
COPY version3.zip /opt
COPY boxplotGeneration.py /opt
COPY find_poly.py /opt
COPY find_poly.sh /opt
COPY poly_create_graph.sh /opt
COPY poly_create_graph.py /opt
COPY translate.sh /opt
COPY translate.py /opt
COPY wich_reference.py /opt
COPY wich_reference.sh /opt
COPY annotate_poly.py /opt
COPY annotate_poly.sh /opt
COPY data_retrieve.sh /opt
# COPY add_taxonomy /opt

# Unzip the file and remove the zip
RUN unzip version3.zip && \
    rm /opt/version3.zip

# Set permissions
RUN chmod 777 *

# Define the command to run your main script
CMD /opt/pre_main

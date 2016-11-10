#!/bin/bash

echo "Starting the remote machine at Digital Ocean..."
vagrant up --provider=digital_ocean

echo "Starting the actual validation..."
vagrant ssh -c "workon validation; cd ~/validation/trollvalidation/trollvalidation; python validations/ice_conc_450_validation.py"

echo "Done with validation, generating the plots..."
vagrant ssh -c "workon validation; cd ~/validation/trollvalidation/trollvalidation; python generate_plots.py"

echo "Compressing the results..."
vagrant ssh -c "cd ~/; tar -zcvf results.tgz ~/validation/data/output/*/*.bmp ~/validation/data/output/*.png ~/validation/data/output/*.csv ~/validation/data/output/*.hdf5 ~/validation/data/input/tmp/*/*.nc"
# vagrant ssh -c "cd ~/; tar -zcvf results.tgz ~/validation/data/output/*.png ~/validation/data/output/*.csv ~/validation/data/output/*.hdf5"

echo "Copying results back to local machine..."
CONTAINER_ID=`vagrant global-status | grep validationdroplet1 | cut -f 1 -d ' '`
vagrant scp ${CONTAINER_ID}:/root/results.tgz ~/Downloads

echo "Destroying droplet, I am done..."
# vagrant destroy

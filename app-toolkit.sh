# For App Development version ii with its own database
# gcloud services list --available
gcloud services enable compute.googleapis.com iam.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com run.googleapis.com aiplatform.googleapis.com cloudresourcemanager.googleapis.com
echo "\n #----------Services have been successfully enabled.----------# \n"

# sh app-dev-ii.sh

# Directory
cd app-toolkit

# App Dev Environment
export APP_DEV_DB_INSTANCE_NAME="matt"

# App Environments
export VERSION="i"
export APP_NAME="app-toolkit-$VERSION"
export DB_PASSWORD="password"
export ADMIN_PASSWORD="password"
export SPECIAL_NAME="guest"
export FIREWALL_RULES_NAME="$APP_NAME-ports"
export DB_PORT=6000

# Create a Database
# Database Environment
export DB_CONTAINER_NAME="$APP_NAME-sql"
# export DB_NAME="$APP_NAME-admin"
export DB_USER="$APP_NAME-admin"
# Remove all running docker
docker rm -f $APP_NAME $DB_CONTAINER_NAME $DB_CONTAINER_NAME-ui
# Remove the db data (only for development)
sudo rm -rf data

# Build
echo "Build the app..."
docker build -t $APP_NAME .

# Run Database Container (Port is different in app-dev-ii)
docker run -d \
    --name $DB_CONTAINER_NAME \
    -e POSTGRES_USER=$DB_USER \
    -e POSTGRES_PASSWORD=$DB_PASSWORD \
    -v $(pwd)/data/:/var/lib/postgresql/data/ \
    -p 6000:5432 \
    postgres
docker run -p 8800:80 \
    --name $DB_CONTAINER_NAME-ui \
    -e 'PGADMIN_DEFAULT_EMAIL=user@example.com' \
    -e 'PGADMIN_DEFAULT_PASSWORD=password' \
    -d dpage/pgadmin4
    

# Environment Variables for the app
DB_HOST=$(gcloud compute instances list --filter="name=$APP_DEV_DB_INSTANCE_NAME" --format="value(networkInterfaces[0].accessConfigs[0].natIP)") 
echo """DB_NAME=$DB_USER
DB_USER=$DB_USER
DB_HOST=$DB_HOST
DB_PORT=$DB_PORT
DB_PASSWORD=$DB_PASSWORD
PROJECT_NAME=$PROJECT_NAME
ADMIN_PASSWORD=$ADMIN_PASSWORD
APP_PORT=$APP_PORT
APP_ADRESS=$APP_ADDRESS
DOMAIN_NAME=$DOMAIN_NAME
SPECIAL_NAME=$SPECIAL_NAME
""" > .env.sh

# Remove docker container
# docker rm -f $APP_NAME

# Run
docker run -d -p 10000:10000 -v $(pwd):/app --env-file .env.sh --name $APP_NAME $APP_NAME

# Create a firewall (GCP)
if gcloud compute firewall-rules list --filter="name=$FIREWALL_RULES_NAME-dev" --format="table(name)" | grep -q $FIREWALL_RULES_NAME-dev; then
    echo "Already created"
else
    gcloud compute --project=$(gcloud config get project) firewall-rules create $FIREWALL_RULES_NAME-dev \
        --direction=INGRESS --priority=1000 --network=default --action=ALLOW --rules=tcp:10000,tcp:8800,tcp:6000 --source-ranges=0.0.0.0/0 
fi

# Remove docker container
# docker rm -f $APP_NAME

# Remove docker container all
# docker rm -f $(docker ps -aq)

# Remove the db data
# sudo rm -rf data

# Docker exec
# docker exec -it $APP_NAME sh

echo "\n #----------DONE----------# \n"


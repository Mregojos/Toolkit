# Directory
cd app-toolkit

# App Dev Environment
export APP_DEV_DB_INSTANCE_NAME="matt"

# App Environments
export VERSION="i"
export APP_NAME="app-dev-ii-multimodal-$VERSION"
export DB_PASSWORD="password"
export ADMIN_PASSWORD="password"
export SPECIAL_NAME="guest"
export FIREWALL_RULES_NAME="$APP_NAME-ports"
export DB_PORT=5000
# Database Environment
export DB_CONTAINER_NAME="$APP_NAME-sql"
# export DB_NAME="$APP_NAME-admin"
export DB_USER="$APP_NAME-admin"

# Remove all running docker
docker rm -f $APP_NAME $DB_CONTAINER_NAME $DB_CONTAINER_NAME-ui
# Remove the db data (only for development)
sudo rm -rf data

# For Dev Firewall Rule
if gcloud compute firewall-rules list --filter="name=$FIREWALL_RULES_NAME-dev" --format="table(name)" | grep -q $FIREWALL_RULES_NAME-dev; then
    gcloud compute firewall-rules delete $FIREWALL_RULES_NAME-dev --quiet
# else
    # echo "$FIREWALL_RULES_NAME-dev Firewall Rule doesn't exist." 
fi
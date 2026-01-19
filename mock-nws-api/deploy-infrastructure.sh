#!/bin/bash
# WaveAlert360 Mock API - Infrastructure Deployment Script
# ========================================================
# Deploys Azure infrastructure using Bicep templates

set -e # Exit on any error

# Configuration
RESOURCE_GROUP_PREFIX="rg-wavealert360"
DEPLOYMENT_NAME="wavealert360-mock-api"
LOCATION="westus2"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Parse command line arguments
ENVIRONMENT=${1:-dev}
OPERATION=${2:-deploy}

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
    log_error "Invalid environment. Use: dev, staging, or prod"
    echo "Usage: $0 <environment> [operation]"
    echo "  environment: dev, staging, prod"
    echo "  operation: deploy, destroy, validate (default: deploy)"
    exit 1
fi

if [[ ! "$OPERATION" =~ ^(deploy|destroy|validate)$ ]]; then
    log_error "Invalid operation. Use: deploy, destroy, or validate"
    exit 1
fi

# Set resource group name
RESOURCE_GROUP="${RESOURCE_GROUP_PREFIX}-${ENVIRONMENT}"

log_info "WaveAlert360 Mock API Infrastructure Deployment"
log_info "Environment: $ENVIRONMENT"
log_info "Operation: $OPERATION"
log_info "Resource Group: $RESOURCE_GROUP"
log_info "Location: $LOCATION"
echo

# Check prerequisites
log_info "Checking prerequisites..."

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    log_error "Azure CLI is not installed. Please install it first."
    echo "Install from: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in to Azure
if ! az account show &> /dev/null; then
    log_warning "Not logged in to Azure. Please log in:"
    az login
fi

# Get current subscription
SUBSCRIPTION=$(az account show --query name -o tsv)
log_info "Using subscription: $SUBSCRIPTION"

# Validate Bicep template
log_info "Validating Bicep template..."
if ! az deployment group validate \
    --resource-group "$RESOURCE_GROUP" \
    --template-file infrastructure/main.bicep \
    --parameters infrastructure/${ENVIRONMENT}.parameters.json \
    --no-prompt &> /dev/null; then
    
    log_error "Bicep template validation failed"
    az deployment group validate \
        --resource-group "$RESOURCE_GROUP" \
        --template-file infrastructure/main.bicep \
        --parameters infrastructure/${ENVIRONMENT}.parameters.json \
        --no-prompt
    exit 1
fi
log_success "Bicep template validation passed"

case $OPERATION in
    "validate")
        log_success "Infrastructure validation completed successfully"
        exit 0
        ;;
        
    "destroy")
        log_warning "This will DELETE all resources in resource group: $RESOURCE_GROUP"
        read -p "Are you sure? Type 'yes' to confirm: " -r
        if [[ $REPLY == "yes" ]]; then
            log_info "Deleting resource group..."
            az group delete --name "$RESOURCE_GROUP" --yes --no-wait
            log_success "Resource group deletion initiated"
        else
            log_info "Destruction cancelled"
        fi
        exit 0
        ;;
        
    "deploy")
        # Create resource group if it doesn't exist
        log_info "Creating resource group if needed..."
        az group create --name "$RESOURCE_GROUP" --location "$LOCATION" --tags \
            project=WaveAlert360 \
            environment="$ENVIRONMENT" \
            managedBy=Bicep \
            createdDate="$(date -u +%Y-%m-%d)" \
            > /dev/null
        
        # Deploy infrastructure
        log_info "Deploying infrastructure..."
        DEPLOYMENT_OUTPUT=$(az deployment group create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$DEPLOYMENT_NAME-$(date +%Y%m%d-%H%M%S)" \
            --template-file infrastructure/main.bicep \
            --parameters infrastructure/${ENVIRONMENT}.parameters.json \
            --query properties.outputs \
            --output json)
        
        if [ $? -eq 0 ]; then
            log_success "Infrastructure deployment completed successfully!"
            echo
            
            # Parse outputs
            FUNCTION_APP_NAME=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.functionAppName.value')
            FUNCTION_APP_URL=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.functionAppUrl.value')
            MOCK_API_BASE=$(echo "$DEPLOYMENT_OUTPUT" | jq -r '.apiEndpoints.value.baseUrl')
            
            # Display deployment results
            log_info "Deployment Results:"
            echo "  📱 Function App: $FUNCTION_APP_NAME"
            echo "  🌐 Function URL: $FUNCTION_APP_URL"
            echo "  🔗 API Base URL: $MOCK_API_BASE"
            echo
            
            # Display API endpoints
            log_info "API Endpoints:"
            echo "  📋 List scenarios: $MOCK_API_BASE/scenarios"
            echo "  🌊 Normal conditions: $MOCK_API_BASE/alerts/active?point=15.2130,145.7545&scenario=normal"
            echo "  🌊 High surf: $MOCK_API_BASE/alerts/active?point=15.2130,145.7545&scenario=high_surf"
            echo "  🌊 Coastal flood: $MOCK_API_BASE/alerts/active?point=15.2130,145.7545&scenario=flood"
            echo
            
            # Update config instructions
            log_info "Next Steps:"
            echo "  1. Deploy function code:"
            echo "     cd mock-nws-api"
            echo "     func azure functionapp publish $FUNCTION_APP_NAME"
            echo
            echo "  2. Update device/config.py:"
            echo "     MOCK_MODE = True"
            echo "     MOCK_API_BASE = \"$MOCK_API_BASE\""
            echo
            echo "  3. Test the deployment:"
            echo "     python device/test_mock_api.py"
            
        else
            log_error "Infrastructure deployment failed"
            exit 1
        fi
        ;;
esac

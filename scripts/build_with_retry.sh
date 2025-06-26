#!/bin/bash

# Build script with retry logic for Docker timeout issues
# Optimized for ML packages like PyTorch and Transformers

set -e

# Configuration
MAX_RETRIES=3
RETRY_DELAY=30
BUILD_TIMEOUT=3600  # 1 hour timeout
DOCKER_BUILDKIT=1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to build with retry
build_with_retry() {
    local service_name=$1
    local dockerfile_path=$2
    local context_path=${3:-"."}
    local attempt=1
    
    print_status "Building $service_name (attempt $attempt/$MAX_RETRIES)"
    
    while [ $attempt -le $MAX_RETRIES ]; do
        print_status "Attempt $attempt: Building $service_name..."
        
        # Set Docker BuildKit for better performance
        export DOCKER_BUILDKIT=$DOCKER_BUILDKIT
        
        # Build command with timeout and optimizations
        if timeout $BUILD_TIMEOUT docker build \
            --progress=plain \
            --no-cache \
            --pull \
            --build-arg BUILDKIT_INLINE_CACHE=1 \
            --build-arg PIP_DEFAULT_TIMEOUT=1000 \
            --build-arg PIP_RETRIES=5 \
            --build-arg PIP_NO_CACHE_DIR=1 \
            -f "$dockerfile_path" \
            -t "sentilyzer-$service_name:latest" \
            "$context_path"; then
            
            print_status "Successfully built $service_name"
            return 0
        else
            print_error "Build failed for $service_name (attempt $attempt/$MAX_RETRIES)"
            
            if [ $attempt -lt $MAX_RETRIES ]; then
                print_warning "Waiting $RETRY_DELAY seconds before retry..."
                sleep $RETRY_DELAY
                
                # Clean up failed build artifacts
                docker system prune -f --filter "until=1h" || true
                
                attempt=$((attempt + 1))
            else
                print_error "All attempts failed for $service_name"
                return 1
            fi
        fi
    done
}

# Function to build all services
build_all_services() {
    print_status "Starting optimized build process for Sentilyzer services"
    
    # Build common dependencies first
    print_status "Building common dependencies..."
    build_with_retry "common" "services/common/Dockerfile" "."
    
    # Build services with ML dependencies
    print_status "Building sentiment processor with ML dependencies..."
    build_with_retry "sentiment-processor" "services/sentiment_processor/Dockerfile" "."
    
    # Build other services
    print_status "Building other services..."
    build_with_retry "data-ingestor" "services/data_ingestor/Dockerfile" "."
    build_with_retry "signals-api" "services/signals_api/Dockerfile" "."
    build_with_retry "twitter-ingestor" "services/twitter_ingestor/Dockerfile" "."
    build_with_retry "dashboard" "services/dashboard/Dockerfile" "services/dashboard"
    
    print_status "All services built successfully!"
}

# Function to build specific service
build_service() {
    local service=$1
    
    case $service in
        "sentiment-processor")
            build_with_retry "sentiment-processor" "services/sentiment_processor/Dockerfile" "."
            ;;
        "data-ingestor")
            build_with_retry "data-ingestor" "services/data_ingestor/Dockerfile" "."
            ;;
        "signals-api")
            build_with_retry "signals-api" "services/signals_api/Dockerfile" "."
            ;;
        "twitter-ingestor")
            build_with_retry "twitter-ingestor" "services/twitter_ingestor/Dockerfile" "."
            ;;
        "dashboard")
            build_with_retry "dashboard" "services/dashboard/Dockerfile" "services/dashboard"
            ;;
        "common")
            build_with_retry "common" "services/common/Dockerfile" "."
            ;;
        *)
            print_error "Unknown service: $service"
            print_status "Available services: sentiment-processor, data-ingestor, signals-api, twitter-ingestor, dashboard, common"
            exit 1
            ;;
    esac
}

# Function to optimize Docker environment
optimize_docker() {
    print_status "Optimizing Docker environment..."
    
    # Clean up old images and containers
    docker system prune -f --filter "until=24h" || true
    
    # Increase Docker daemon timeout
    print_status "Docker environment optimized"
}

# Function to show help
show_help() {
    echo "Usage: $0 [OPTIONS] [SERVICE]"
    echo ""
    echo "Build Sentilyzer Docker services with retry logic and timeout optimization"
    echo ""
    echo "OPTIONS:"
    echo "  -h, --help     Show this help message"
    echo "  -a, --all      Build all services (default)"
    echo "  -s, --service  Build specific service"
    echo "  -o, --optimize Optimize Docker environment before building"
    echo ""
    echo "SERVICES:"
    echo "  sentiment-processor  Build sentiment processor with ML dependencies"
    echo "  data-ingestor       Build data ingestor service"
    echo "  signals-api         Build signals API service"
    echo "  twitter-ingestor    Build Twitter ingestor service"
    echo "  dashboard           Build dashboard service"
    echo "  common              Build common dependencies"
    echo ""
    echo "EXAMPLES:"
    echo "  $0                                    # Build all services"
    echo "  $0 -s sentiment-processor            # Build only sentiment processor"
    echo "  $0 -o -a                            # Optimize Docker then build all"
    echo ""
}

# Main script logic
main() {
    local build_all=true
    local service=""
    local optimize=false
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -a|--all)
                build_all=true
                shift
                ;;
            -s|--service)
                build_all=false
                service="$2"
                shift 2
                ;;
            -o|--optimize)
                optimize=true
                shift
                ;;
            *)
                if [[ $build_all == true ]]; then
                    # If no flags specified, treat as service name
                    build_all=false
                    service="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Optimize Docker if requested
    if [[ $optimize == true ]]; then
        optimize_docker
    fi
    
    # Build services
    if [[ $build_all == true ]]; then
        build_all_services
    else
        if [[ -z $service ]]; then
            print_error "No service specified"
            show_help
            exit 1
        fi
        build_service "$service"
    fi
    
    print_status "Build process completed successfully!"
}

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Run main function
main "$@" 
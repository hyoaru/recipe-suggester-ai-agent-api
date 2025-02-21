pipeline {
  agent any

  environment {
    sanitized_branch_name = env.BRANCH_NAME.replaceAll('/', '-')
    API_TESTS_REPO_URL = 'https://github.com/hyoaru/recipe-suggester-ai-agent-api-tests.git'

    DOCKER_NETWORK_NAME = "recipe_suggester_ai_agent_network_${env.sanitized_branch_name}_${env.BUILD_ID}"
    DOCKER_CONTAINER_NAME_API = "recipe_suggester_ai_agent_api_${env.sanitized_branch_name}_${env.BUILD_ID}"
    DOCKER_IMAGE_NAME_API = 'recipe_suggester_ai_agent_api'
    DOCKER_IMAGE_NAME_API_TESTS = 'recipe_suggester_ai_agent_api_tests'
    DOCKER_IMAGE_NAME_API_PRODUCTION = "recipe_suggester_ai_agent_api_production_build_${env.BUILD_ID}"
    DOCKER_CONTAINER_NAME_API_PRODUCTION = "recipe_suggester_ai_agent_api_production"

    // Services environment variables
    OPENAI_API_KEY = credentials('OPENAI_API_KEY')
    API_BASE_URL = "http://${env.DOCKER_CONTAINER_NAME_API}:7000"
  }

  options {
    // Required step for cleaning before build
    skipDefaultCheckout(true)
  }

  stages {
    stage('Clean Workspace') {
      steps {
        script {
          echo 'Cleaning workspace...'
          cleanWs()
          echo 'Cleaned the workspace.'
        }
      }
    }

    stage("Checkout Source Codes") {
      parallel {
        stage('Checkout API Source Code') {
          steps {
            dir('api') {
              echo 'Checking out source code...'
              checkout scm
              echo 'Checked out source code.'
            }
          }
        }

        stage('Checkout API-Tests Source Code') {
          steps {
            dir('api-tests') {
              echo 'Cloning API-Tests repository...'
              git branch: 'master', url: env.API_TESTS_REPO_URL
              echo 'Checked out API-Tests source code.'
            }
          }
        }
      }
    }

    stage("Populate Environment Variables") {
      parallel {
        stage('Populate Api Environment Variables') {
          steps {
            script {
              writeEnvFile("./api", [
                "OPENAI_API_KEY=${env.OPENAI_API_KEY}"
              ])
            }
          }
        }

        stage('Populate Api-Tests Environment Variables') {
          steps {
            script {
              writeEnvFile("./api-tests", [
                "API_BASE_URL=${env.API_BASE_URL}"
              ])
            }
          }
        }
      }
    }

    stage('Build Docker Images') {
      steps {
        echo 'Building Docker images...'
        sh 'echo "Using docker version: $(docker --version)"'

        script {
          buildDockerImage('./api', env.DOCKER_IMAGE_NAME_API)
          buildDockerImage('./api-tests', env.DOCKER_IMAGE_NAME_API_TESTS)
        }

        sh 'docker images'
        echo 'Docker images built'
      }
    }

    stage('Run API') {
      steps {
        echo "Creating docker network for API: ${env.DOCKER_NETWORK_NAME}..."
        sh "docker network create ${env.DOCKER_NETWORK_NAME}"
        echo 'Docker network created.'

        script { runApiContainer('test') }
        sh 'docker ps -a'
      }
    }

    stage('Run Smoke Tests') {
      when {
        anyOf {
          branch 'develop'
          expression { env.BRANCH_NAME.startsWith('feature') }
        }
      }

      steps {
        echo 'Smoke tests pending...'

        script {
          try {
            runRobotTests('smoke')
          } catch (Exception e) { }
        }

        echo 'Smoke tests done.'
      }
    }


    stage('Run Full Tests') {
      when {
        anyOf {
          branch 'master'
          expression { env.BRANCH_NAME.startsWith('release') }
        }
      }

      steps {
        echo "Full tests pending..."

        script {
          try {
            runRobotTests('all')
          } catch (Exception e) { }
        }

        echo 'Full tests done.'
      }
    }

    stage('Publish Test Reports') {
      steps {
        dir('./api-tests') {
          robot(
            outputPath: "./results",
            passThreshold: 90.0,
            unstableThreshold: 80.0,
            disableArchiveOutput: true,
            outputFileName: "output.xml",
            logFileName: 'log.html',
            reportFileName: 'report.html',
            countSkippedTests: true,
          )
        }
      }
    }

    stage ('Build Docker Image For Production') {
      when {
        branch 'master'
      }

      steps {
        echo 'Building api docker image for production...'
        sh 'echo "Using docker version: $(docker --version)'

        script {
          buildDockerImage('./api', env.DOCKER_IMAGE_NAME_API_PRODUCTION)
        }

        sh 'docker images'
        echo 'Docker api image for production built.'
      }
    }


    stage ('Deploy') {
      when {
        branch 'master'
      }

      steps {
        script {
          // Stop the production api container to then run the rebuilt image
          stopApiContainer('production')
          runApiContainer('production')
        }
      }
    }
  }


  post {
    always {
      echo "Job name: ${env.JOB_NAME}"
      echo "Build url: ${env.BUILD_URL}"
      echo "Build id: ${env.BUILD_ID}"
      echo "Build display name: ${env.BUILD_DISPLAY_NAME}"
      echo "Build number: ${env.BUILD_NUMBER}"
      echo "Build tag: ${env.BUILD_TAG}"

      script {
        def causes = currentBuild.getBuildCauses()
        causes.each { cause ->
          echo "Build cause: ${cause.shortDescription}"
        }

        stopApiContainer('test')
        cleanDanglingImages()
        sh "docker network rm ${DOCKER_NETWORK_NAME}"


        // Prune images every 5 builds based on BUILD_ID
        if (env.BUILD_ID.toInteger() % 5 == 0) {
          echo "Pruning old Docker images..."
          sh 'yes | docker image prune -a'
        }
      }
    }
  }
}


void cleanDanglingImages() {
  sh '''
    danglingImages=$(docker images -f "dangling=true" -q)
    if [ -n "$danglingImages" ]; then
      docker image rmi $danglingImages
    else
      echo "No dangling images to remove."
    fi
  '''
}

void runRobotTests(String testType) {
  dir('./api-tests') {
    docker.image(env.DOCKER_IMAGE_NAME_API_TESTS).inside("--network=${env.DOCKER_NETWORK_NAME}") {
      echo 'Running health check...'
      sh "curl ${env.DOCKER_CONTAINER_NAME_API}:7000/api/operations/health"

      if (testType != 'all') {
        sh "robot --include ${testType} --outputdir ./results ./tests/suites"
      } else {
        sh "robot --outputdir ./results ./tests/suites"
      }
    }
  }
}

void stopApiContainer(String environment) {
  if (environment == 'production') {
    echo "Stopping production API with container name: ${env.DOCKER_CONTAINER_NAME_API_PRODUCTION}..."
    sh "docker stop ${env.DOCKER_CONTAINER_NAME_API_PRODUCTION}"
  } else if (environment == 'test') {
    echo "Stopping test API with container name: ${env.DOCKER_CONTAINER_NAME_API}..."
    sh "docker stop ${env.DOCKER_CONTAINER_NAME_API}"
  } else {
    error "Invalid environment specified: ${environment}. Please use 'production' or 'test'."
  }
  echo 'Stopped API.'
}

void runApiContainer(String environment) {
  echo "Starting ${environment} environment API container..."

  dir ('./api') {
    if (environment == 'production') {
      sh """
        docker run -d --rm \
          --name ${env.DOCKER_CONTAINER_NAME_API_PRODUCTION} \
          --network host \
          -v \$(pwd):/app \
          ${env.DOCKER_IMAGE_NAME_API_PRODUCTION} 
      """
    } else if (environment == 'test') {
      sh """
        docker run -d --rm \
          --name ${env.DOCKER_CONTAINER_NAME_API} \
          --network=${env.DOCKER_NETWORK_NAME} \
          -v \$(pwd):/app \
          ${env.DOCKER_IMAGE_NAME_API} fastapi run main.py --host 0.0.0.0 --port 7000
      """
    } else {
      error "Invalid environment specified: ${environment}. Please use 'production' or 'test'."
    }
  }

  echo 'Waiting for API to start...'
  sleep 5
  echo 'Started API.'
}

void writeEnvFile(String directory, List<String> variables) {
  dir(directory) {
    echo "Writing .env file at ${directory}..."
    writeFile file: '.env', text: variables.join('\n')
    echo "Environment file created successfully at ${directory}."
  }
}

void buildDockerImage(String directory, String imageName) {
  dir(directory) {
    echo "Building ${imageName} image..."
    sh "docker build -t ${imageName} ."
    echo "${imageName} image built."
  }
}

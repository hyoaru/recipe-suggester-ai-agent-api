pipeline {
  agent any

  environment {
    sanitized_branch_name = env.BRANCH_NAME.replaceAll('/', '-')

    DOCKER_NETWORK_NAME = "recipe_suggester_ai_agent_network_${env.sanitized_branch_name}_${env.BUILD_ID}"
    DOCKER_CONTAINER_NAME_API = "recipe_suggester_ai_agent_api_${env.sanitized_branch_name}_${env.BUILD_ID}"
    DOCKER_IMAGE_NAME_API = 'recipe_suggester_ai_agent_api'
    DOCKER_IMAGE_NAME_API_TESTS = 'recipe_suggester_ai_agent_api_tests'
    DOCKER_IMAGE_NAME_API_PRODUCTION = "recipe_suggester_ai_agent_api_production_build_${env.BUILD_ID}"
    DOCKER_CONTAINER_NAME_API_PRODUCTION = "recipe_suggester_ai_agent_api_production"
  }

  options {
    // Required step for cleaning before build
    skipDefaultCheckout(true)
  }

  stages {
    stage('Setup and Environment Preparation') {
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
              environment {
                API_TESTS_REPO_URL = 'https://github.com/hyoaru/recipe-suggester-ai-agent-api-tests.git'
              }
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
              environment {
                OPENAI_API_KEY = credentials('OPENAI_API_KEY')
              }
              steps {
                script {
                  writeEnvFile("./api", [
                    "OPENAI_API_KEY=${env.OPENAI_API_KEY}"
                  ])
                }
              }
            }

            stage('Populate Api-Tests Environment Variables') {
              environment {
                API_BASE_URL = "http://${env.DOCKER_CONTAINER_NAME_API}:7000"
              }
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
      }
    }

    stage('Run Tests and Quality Analysis') {
      parallel {
        stage('Run Tests') {
          when {
            anyOf {
              expression { env.BRANCH_NAME.startsWith('feature') }
              expression { script{ env.BRANCH_NAME.startsWith('feature') && env.CHANGE_TARGET == 'develop' } }
              expression { script{ env.BRANCH_NAME.startsWith('release') && env.CHANGE_TARGET == 'master' } }
              branch 'master'
            }
          }

          stages {
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

            stage('Run Robot Smoke Tests') {
              when {
                expression { env.BRANCH_NAME.startsWith('feature') }
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


            stage('Run Robot Regression Tests') {
              when {
                anyOf {
                  expression { script{ env.BRANCH_NAME.startsWith('feature') && env.CHANGE_TARGET == 'develop' } }
                  expression { script{ env.BRANCH_NAME.startsWith('release') && env.CHANGE_TARGET == 'master' } }
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

            stage('Run Robot Full Tests') {
              when { branch 'master' }

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

            stage('Publish Robot Test Reports') {
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
          }
        }

        stage('Quality and Security Analysis') {
          when {
            anyOf {
              expression { script { env.BRANCH_NAME?.startsWith('feature') && env.CHANGE_TARGET == 'develop' } }
              expression { script { env.BRANCH_NAME?.startsWith('release') && env.CHANGE_TARGET == 'master' } }
              branch 'master'
            }
          }

          stages {
            stage ('Run SonarQube Analysis') {
              environment {
                SONAR_SCANNER = tool name: 'SonarQubeScanner-7.0.2'
                SONAR_PROJECT_KEY = "recipe-suggester-ai-agent-api"
              }

              steps {
                dir('./api') {
                  withSonarQubeEnv('SonarQube') {
                    sh "${SONAR_SCANNER}/bin/sonar-scanner -Dsonar.projectKey=${env.SONAR_PROJECT_KEY}"
                  }
                }
              }
            }

            stage('Quality Gate') {
              steps {
                script {
                  timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                  }
                }
              }
            }
          }
        }
      }
    }

    stage('Deploy to Production') {
      when { branch 'master' }
      stages {
        stage ('Build Docker Image For Production') {
          steps {
            echo 'Building api docker image for production...'
            sh 'echo "Using docker version: $(docker --version)"'

            script {
              buildDockerImage('./api', env.DOCKER_IMAGE_NAME_API_PRODUCTION)
            }

            sh 'docker images'
            echo 'Docker api image for production built.'
          }
        }


        stage ('Deploy') {
          steps {
            script {
              // Stop the production api container to then run the rebuilt image
              stopApiContainer('production')
              runApiContainer('production')
            }
          }
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
      echo "Branch name: ${env.BRANCH_NAME}"

      script {
        if (env.CHANGE_TARGET) {
          echo "Pull request from `${env.CHANGE_BRANCH}` to `${env.CHANGE_TARGET}`"
        }
      }

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
        sh "pabot --include ${testType} --outputdir ./results --testlevelsplit ./tests/suites"
      } else {
        sh "pabot --outputdir ./results --testlevelsplit ./tests/suites"
      }
    }
  }
}

void stopApiContainer(String environment) {
  String containerName

  if (environment == 'production') {
    containerName = env.DOCKER_CONTAINER_NAME_API_PRODUCTION
    echo "Stopping production API with container name: ${containerName}..."
  } else if (environment == 'test') {
    containerName = env.DOCKER_CONTAINER_NAME_API
    echo "Stopping test API with container name: ${containerName}..."
  } else {
    error "Invalid environment specified: ${environment}. Please use 'production' or 'test'."
  }

  // Check if the container exists
  def containerExists = sh(script: "docker ps -q -f name=${containerName}", returnStdout: true).trim()

  if (containerExists) {
    sh "docker stop ${containerName}"
    echo 'Stopped API.'
  } else {
    echo "Container ${containerName} does not exist. No action taken."
  }
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

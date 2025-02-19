pipeline {
  agent any

  triggers {
    githubPush()
  }

  environment {
    OPENAI_API_KEY = credentials('OPENAI_API_KEY')
    API_BASE_URL = "http://localhost:7000"
    API_TESTS_REPO_URL = "https://github.com/hyoaru/recipe-suggester-ai-agent-api-tests"
  }


  options {
    // Required step for cleaning before build
    skipDefaultCheckout(true)
  }

  stages {
    stage('Clean Workspace') {
      steps {
        echo "Cleaning workspace..."
        cleanWs()
        echo "Cleaned the workspace."
      }
    }

    stage("Checkout Source Codes") {
      parallel {
        stage('Checkout API Source Code') {
          steps {
            dir('api') {
              echo "Checking out source code..."
              checkout scm
              echo "Checked out source code."
            }
          }
        }


        stage('Checkout API-Tests Source Code') {
          steps {
            dir('api-tests') {
              echo "Cloning API-Tests repository..."
              git branch: 'master', url: "${env.API_TESTS_REPO_URL}"
              echo "Checked out API-Tests source code."
            }
          }
        }
      }
    }

    stage("Populate Environment Variables") {
      parallel {
        stage('Populate Api Environment Variables') {
          steps {
            dir ('./api') {
              script {
                echo "Populating the API environment variables..."
                def envContent = """
                  OPENAI_API_KEY=${env.OPENAI_API_KEY}
                """.stripIndent()

                writeFile file: '.env', text: envContent
                echo "Api environment file (.env) created succesfully."
              }
            }
          }
        }

        stage('Populate Api-Tests Environment Variables') {
          steps {
            dir ('./api-tests') {
              script {
                echo "Populating the API-Tests environment variables..."
                def envContent = """
                  API_BASE_URL=${env.API_BASE_URL}
                """.stripIndent()

                writeFile file: '.env', text: envContent
                echo "Api-Tests environment file (.env) created succesfully."
              }
            }
          }
        }
      }
    }

    stage('Build Docker Images') {
      steps {
        echo "Building Docker images..."
        sh 'echo "Using docker version: $(docker --version)"'

        dir('./api') {
          sh '''
            echo "Building api image..."
            docker build -t recipe_suggester_ai_agent_api .
            echo "Api image built."
          '''
        }

        dir('./api-tests') {
          sh '''
            echo "Building api tests image..."
            docker build -t recipe_suggester_ai_agent_api_tests .
            echo "Api tests image built."
          '''
        }

        sh 'docker images'
        echo "Building images built."
      }
    }

    stage('Run API') {
      steps {
        dir('./api') {
          sh '''
            echo "Current directory: $(pwd)"
            ls -al

            echo "Starting API..."

            docker run -d --rm \
              --name recipe_suggester_ai_agent_api \
              --network=host \
              -v $(pwd):/app \
              recipe_suggester_ai_agent_api fastapi run main.py --host 0.0.0.0 --port 7000
            
            echo "Waiting for API to start..."
            sleep 5
            docker ps -a
          '''

          sh "curl ${env.API_BASE_URL}"
          sh 'echo "API started"'
        }
      }
    }

    stage('Run Tests') {
      steps {
        dir('./api-tests') {
          sh '''
            echo "Current directory: $(pwd)"
            ls -al
          '''
          
          echo "Checking API health..."
          sh "curl ${env.API_BASE_URL}/api/operations/health"

          sh '''
            echo "Running tests..."

            docker run --rm \
              --name recipe_suggester_ai_agent_api_tests \
              --network=host \
              -v $(pwd):/app \
              recipe_suggester_ai_agent_api_tests robot --outputdir ./results ./tests/suites

            echo "Tests completed."
          '''
        }
      }
    }

    stage('Stop API') {
      steps {
        dir('./api') {
          sh '''
            echo "Current directory: $(pwd)"
            ls -al

            echo "Stopping API..."
            docker stop recipe_suggester_ai_agent_api
            echo "API stopped"
          '''
        }
      }
    }


  }
}
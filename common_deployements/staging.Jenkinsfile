pipeline {
    agent any

    environment {
        DEPLOYMENT_ENV = 'staging'
    }

    stages {
        stage('Setup') {
            steps {
                echo 'Starting build with the following env:'
                sh "printenv"
                echo "\n"
                echo "Copying over '${DEPLOYMENT_ENV}' environment specific config for core submodule..."
                sh "cp core/utilities/constants.${DEPLOYMENT_ENV}.py core/utilities/constants.py"
            }
        }
        stage('Build') {
            steps {
                googleCloudBuild \
                    credentialsId: "${GCP_OAUTH_CREDENTIAL_ID}",
                    source: local("."),
                    request: file("build/cloudbuild.yaml"),
                    substitutions: [
                        _IMAGE_NAME: "${JOB_NAME}",
                        _IMAGE_TAG: "${BUILD_NUMBER}"
                    ]
            }
        }
        stage('Deployment') {
            steps {

                withKubeCredentials(kubectlCredentials: [[clusterName: "$K8S_CLUSTER_NAME", credentialsId: "$K8S_CLUSTER_CREDENTIAL"]]) {
                    sh "./build/helmdeploy.sh"
                }
            }
        }
        stage('Verification') {
            steps {
                // TODO: Add rollout status check using helm
                echo "Manually verify the deployment!"
            }
        }
    }
    post {
        always {
            cleanWs()
        }
    }
}

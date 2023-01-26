pipeline {
    agent {
        label 'utility'
    }

    environment{
        SLACK_CHANNEL = '#platform-engineering-ci'
        PRIVATE_PYPI = "https://mirror-sac0-0000.backblaze.com/pypi/bz/uploads"

    }

    options {
        disableConcurrentBuilds()
        timeout(time: 10, unit: 'MINUTES')
    }

    stages {
        stage('Notify Build') {
            steps {
                script {
                    commit = sh(script: "git log -1 --pretty=format:'%an: %s'", returnStdout: true).trim()
                    hash = sh(script: "git log -1 --pretty=%h", returnStdout: true).trim()
                    slackSend(
                        color: "#6ECADC", // blue
                        channel: env.SLACK_CHANNEL,
                        message: "Started job: *${currentBuild.fullDisplayName}* \nNode: ${env.NODE_NAME} \nExecutor: ${env.EXECUTOR_NUMBER} \nURL: <${env.BUILD_URL}|${env.BUILD_DISPLAY_NAME}> \n Commit: [<https://github.com/Backblaze/migration_dash/commit/${env.GIT_COMMIT}|${hash}>] ${commit}"
                    )
                }
            }
        }

        stage('Virtual Environment') {
            environment {
                PYTHON = '/usr/local/bin/python3'
            }
            steps {
                sh "./create_venv.sh"
            }
        }

        stage('Lint') {
            steps {
                sh 'venv/bin/black --check source'
                sh 'venv/bin/pyre check'
            }
        }

        stage('Publish PyPI Artifact') {
            when {
                branch "main"
            }
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'devpi_bz',
                    usernameVariable: 'TWINE_USERNAME',
                    passwordVariable: 'TWINE_PASSWORD'
                )]) {
                    sh '''
                        git clean -qfd  # we clean so that we don't flag our build as dirty.
                        ./pypi_publish.sh "${PRIVATE_PYPI}"
                    '''
                }
            }
        }
    }

    post {
        always {
            jiraSendBuildInfo site: 'backblaze.atlassian.net'
        }
        failure {
            slackSend(
                color: "#E01563",   // red
                channel: env.SLACK_CHANNEL,
                message: "Build failed: *${currentBuild.fullDisplayName}* \nURL: <${env.BUILD_URL}|${env.BUILD_DISPLAY_NAME}> \nDuration: ${currentBuild.durationString.replace(' and counting', '')}"
            )
        }
        aborted {
            slackSend(
                color: "#FFC300",   // yellow
                channel: env.SLACK_CHANNEL,
                message: "Build aborted: *${currentBuild.fullDisplayName}* \nURL: <${env.BUILD_URL}|${env.BUILD_DISPLAY_NAME}> \nDuration: ${currentBuild.durationString.replace(' and counting', '')}"
            )
        }
        success {
            slackSend(
                color: "#3EB991",   // green
                channel: env.SLACK_CHANNEL,
                message: "Build succeeded: *${currentBuild.fullDisplayName}* \nURL: <${env.BUILD_URL}|${env.BUILD_DISPLAY_NAME}> \nDuration: ${currentBuild.durationString.replace(' and counting', '')}"
            )
        }
    }
}

/*
 * This is a high level diagram visualizing when the Credentials IDA emits a "program completion email". It is written
 * using Structurizr DSL (https://structurizr.org/).
 */
workspace {
    model {
        learner = person "Learner" "A learner taking courses on Open edX site"

        lms = softwareSystem "edx-platform LMS"

        group "Credentials IDA" {
            credentials_app = softwareSystem "Credentials Django App"
            api_app = softwareSystem "API Django App"
            edx_ace = softwareSystem "edX ACE App"
        }

        learner -> lms "Earns passing grade in final course of a program"
        lms -> api_app "Makes API request to award program certificate to learner"
        api_app -> credentials_app "Issues Program Credential to learner"
        credentials_app -> credentials_app "Determine if email should be sent based on Program completion"
        credentials_app -> edx_ace "Personalizes email based on message template and config"
        edx_ace -> learner "Sends congratulatory message to learner"

    }

    views {
        systemlandscape "SystemLandscape" {
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                shape Person
            }
        }
    }
}

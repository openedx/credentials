/*
 * This is a high level diagram visualizing how a learner can access their program records and how data is retreived.
 * It is written using Structurizr DSL (https://structurizr.org/).
 */
workspace {
    model {
        learner = person "Learner" "Registered learner on Open edX site"

        group "edx-platform LMS" {
            program_dashboard = softwareSystem "Program Dashboard (Legacy FE)"
        }

        group "Credentials IDA" {
            records_app = softwareSystem "Records Django App"
        }

        profile_mfe = softwareSystem "(User) Profile MFE"
        lr_mfe = softwareSystem "Learner Record MFE"

        learner -> program_dashboard "views their Program Dashboard"
        learner -> profile_mfe "views their user Profile"

        program_dashboard -> records_app "clicks `View Program Record` button"
        profile_mfe -> records_app "clicks `View my Records` button"

        records_app -> lr_mfe "Learner redirected to"
        lr_mfe -> records_app "REST API call to"
        lr_mfe -> learner "Renders program record info for"
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

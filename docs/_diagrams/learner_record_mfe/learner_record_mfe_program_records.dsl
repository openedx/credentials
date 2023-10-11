/*
 * This is a high level diagram visualizing how the system retrieves information about a learner's progress in a
 * specific program. It is written using Structurizr DSL (https://structurizr.org/).
 */
workspace {
    model {
        learner = person "Learner" "Registered learner on Open edX site"

        group "Credentials IDA" {
            catalog_app = softwareSystem "Catalog Django App"
            core_app = softwareSystem "Core Django App"
            credentials_app = softwareSystem "Credentials Django App"
            records_app = softwareSystem "Records Django App"
        }

        lr_mfe = softwareSystem "Learner Record MFE"

        learner -> lr_mfe "clicks `View Program Record` button"
        lr_mfe -> records_app "REST API to retrieve program progress data"
        records_app -> core_app "retrieves user info"
        records_app -> catalog_app "retrieves pathway info"
        records_app -> credentials_app "retrieves credential info"
        records_app -> records_app "retrieves grade and sharing info"
        records_app -> lr_mfe "returns program record info"
        lr_mfe -> learner "renders program record for"
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

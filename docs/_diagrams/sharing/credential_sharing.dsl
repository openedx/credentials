/*
 * C4 model for the Credential Sharing feature in Open edX.
 * Covers Digital Badges and Verifiable Credentials.
 *
 * Written in Structurizr DSL (https://structurizr.org/).
 */
workspace "Credential Sharing" {

    model {
        siteAdmin = person "Site Admin" "Configures badge templates and VC issuing"
        learner = person "Learner" "Earns credentials through learning activities"
        verifier = person "Verifier" "Employer or institution that verifies learner credentials"

        digitalWallet = softwareSystem "Digital Wallet" "Learner Credential Wallet or compatible storage"
        digitalBadgePlatform = softwareSystem "Digital Badge Platform" "Credly, Accredible" "Existing System"

        openedX = softwareSystem "Open edX" {
            edxPlatform = container "openedx-platform" "LMS and course management" "Python/Django"
            eventBus = container "Event Bus" "Redis Streams or Kafka" "" "Queue"
            credentialsService = container "edX Credentials" "Stores learner achievements, issues credentials" "Python/Django" {
                credentialsCore = component "Credentials Core" "Manages course and program certificates" "Django"
                digitalBadgesIssuer = component "Digital Badges Issuer" "Processes badge requirements, issues badges to external platforms" "Django"
                verifiableCredentialsIssuer = component "Verifiable Credentials Issuer" "Issues W3C Verifiable Credentials, signs with didkit (Ed25519)" "Django"
                vcIssuerMFE = component "Learner Record MFE" "UI for learners to request verifiable credentials" "React"
            }
            credentialsDB = container "MySQL" "Credentials database" "" "Database"
        }

        # --- Actors ---

        siteAdmin -> credentialsCore "Configures badge templates and VC settings" "Admin panel"
        learner -> edxPlatform "Completes courses and assignments"
        learner -> vcIssuerMFE "Requests verifiable credential"

        # --- Event Bus flows ---

        # LMS produces events consumed by Credentials
        edxPlatform -> eventBus "Publishes certificate and course passing status events" "openedx-events"
        eventBus -> credentialsCore "Delivers certificate and course grades events" "openedx-events"
        eventBus -> digitalBadgesIssuer "Delivers badge-related events" "learning-badges-lifecycle topic"

        # Credentials produces events back to the bus
        digitalBadgesIssuer -> eventBus "Publishes badges lifecycle events" "openedx-events"

        # --- Internal flows ---

        credentialsCore -> credentialsDB "Uses" "Django ORM"
        digitalBadgesIssuer -> credentialsDB "Uses" "Django ORM"
        verifiableCredentialsIssuer -> credentialsDB "Uses" "Django ORM"

        # --- External integrations ---

        # Badges
        digitalBadgesIssuer -> digitalBadgePlatform "Issues and revokes badges" "REST API"

        # Verifiable Credentials
        vcIssuerMFE -> verifiableCredentialsIssuer "Initiates VC issuance"
        verifiableCredentialsIssuer -> digitalWallet "Sends signed verifiable credential"
        digitalWallet -> verifiableCredentialsIssuer "Sends issuance request" "HTTP"

        # Verification
        verifier -> verifiableCredentialsIssuer "Checks credential revocation status" "StatusList2021 API"
        verifier -> digitalBadgePlatform "Checks badge revocation status" ""

    }

    views {
        systemContext openedX "SystemContext" "High-level view of Credential Sharing" {
            include *
            autoLayout lr
        }

        container openedX "Containers" "Open edX containers involved in credential sharing" {
            include *
            autoLayout lr
        }

        component credentialsService "Components" "Credentials service internal components" {
            include *
            autoLayout lr
        }

        styles {
            element "Person" {
                color "#ffffff"
                background "#08427b"
                fontSize 22
                shape Person
            }
            element "Software System" {
                background "#1168bd"
                color "#ffffff"
            }
            element "Existing System" {
                background "#999999"
                color "#ffffff"
            }
            element "Container" {
                background "#438dd5"
                color "#ffffff"
            }
            element "Component" {
                background "#85bbf0"
                color "#000000"
            }
            element "Database" {
                shape Cylinder
            }
            element "Queue" {
                shape Pipe
            }
        }
    }
      configuration {
        scope softwaresystem
    }
}

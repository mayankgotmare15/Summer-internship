pluginManagement {
    includeBuild("build-logic")
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "RouteDesk"

// Application
include(":app")

// Core Modules
include(":core:model")
include(":core:network")
include(":core:auth")
include(":core:database")
include(":core:data")
include(":core:designsystem")
include(":core:ui")
include(":core:notifications")
include(":core:testing")

// Feature Modules
include(":feature:auth")
include(":feature:home")
include(":feature:intake")
include(":feature:tickets")
include(":feature:escalation")
include(":feature:work")
include(":feature:review")
include(":feature:team")
include(":feature:approvals")
include(":feature:insights")
include(":feature:notifications")
include(":feature:help")
include(":feature:profile")

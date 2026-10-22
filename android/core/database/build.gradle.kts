plugins {
    id("routedesk.android.library")
    id("routedesk.android.room")
    id("routedesk.android.hilt")
}

android {
    namespace = "com.routedesk.database"
}

dependencies {
    implementation(project(":core:model"))

    implementation(libs.kotlinx.datetime)
    implementation(libs.kotlinx.serialization.json)
    implementation(libs.androidx.paging.runtime)
}

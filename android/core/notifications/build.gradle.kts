plugins {
    id("routedesk.android.library")
    id("routedesk.android.hilt")
}

android {
    namespace = "com.routedesk.notifications"
}

dependencies {
    implementation(project(":core:model"))
    implementation(project(":core:data"))

    implementation(platform(libs.firebase.bom))
    implementation(libs.firebase.messaging)
    implementation(libs.androidx.core.ktx)
}

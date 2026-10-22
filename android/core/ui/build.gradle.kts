plugins {
    id("routedesk.android.library")
    id("routedesk.android.compose")
}

android {
    namespace = "com.routedesk.ui"
}

dependencies {
    implementation(project(":core:model"))
    implementation(project(":core:designsystem"))

    implementation(libs.coil.compose)
    implementation(libs.coil.network.okhttp)
    implementation(libs.kotlinx.datetime)
}

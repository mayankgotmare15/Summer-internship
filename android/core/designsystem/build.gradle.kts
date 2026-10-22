plugins {
    id("routedesk.android.library")
    id("routedesk.android.compose")
}

android {
    namespace = "com.routedesk.designsystem"
}

dependencies {
    implementation(libs.androidx.compose.material.icons)
}

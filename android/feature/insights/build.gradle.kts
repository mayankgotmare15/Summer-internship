plugins {
    id("routedesk.android.feature")
}

android {
    namespace = "com.routedesk.feature.insights"
}

dependencies {
    implementation(libs.vico.compose)
    implementation(libs.vico.compose.m3)
}

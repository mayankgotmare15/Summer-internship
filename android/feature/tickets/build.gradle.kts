plugins {
    id("routedesk.android.feature")
}

android {
    namespace = "com.routedesk.feature.tickets"
}

dependencies {
    implementation(libs.androidx.paging.compose)
}

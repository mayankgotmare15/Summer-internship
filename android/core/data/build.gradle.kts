plugins {
    id("routedesk.android.library")
    id("routedesk.android.hilt")
}

android {
    namespace = "com.routedesk.data"
}

dependencies {
    implementation(project(":core:model"))
    implementation(project(":core:network"))
    implementation(project(":core:database"))
    implementation(project(":core:auth"))

    implementation(libs.androidx.work.runtime.ktx)
    implementation(libs.androidx.paging.runtime)
    implementation(libs.hilt.work)
    ksp(libs.hilt.work.compiler)
}

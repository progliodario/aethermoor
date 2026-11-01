// Pure Kotlin/JVM module: simulation, data and world generation. No Android or libGDX imports allowed.
plugins {
    alias(libs.plugins.kotlin.jvm)
}

kotlin {
    jvmToolchain(17)
}

dependencies {
    implementation(libs.kotlinx.serialization.json)
    testImplementation(platform(libs.junit.bom))
    testImplementation(libs.junit.jupiter)
    testRuntimeOnly(libs.junit.platform.launcher)
}

tasks.test {
    useJUnitPlatform()
    // Shared conformance vectors and the base pack live at the repository root.
    systemProperty("aether.repoRoot", rootProject.projectDir.parentFile.absolutePath)
}

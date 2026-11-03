import org.jetbrains.kotlin.gradle.dsl.JvmTarget

// libGDX layer: rendering, audio, input, UI. Depends on :core, never the other way round.
plugins {
    alias(libs.plugins.android.library)
    alias(libs.plugins.kotlin.android)
}

android {
    namespace = "io.github.progliodario.aethermoor.game"
    compileSdk = 35

    defaultConfig {
        minSdk = 30
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

kotlin {
    compilerOptions {
        jvmTarget.set(JvmTarget.JVM_17)
    }
}

dependencies {
    api(project(":core"))
    api(libs.gdx)
}

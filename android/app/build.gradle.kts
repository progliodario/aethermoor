import groovy.json.JsonSlurper

plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
}

// Single source of truth for name, version and application id: <repo root>/project.json
@Suppress("UNCHECKED_CAST")
val projectMeta = JsonSlurper().parse(rootProject.file("../project.json")) as Map<String, Any>
val gameName = projectMeta["name"] as String
val gameVersion = projectMeta["version"] as String
val gameApplicationId = projectMeta["application_id"] as String

android {
    namespace = "io.github.progliodario.aethermoor.app"
    compileSdk = 35

    defaultConfig {
        applicationId = gameApplicationId
        minSdk = 30
        targetSdk = 35
        versionCode = 1
        versionName = gameVersion
        buildConfigField("String", "GAME_NAME", "\"$gameName\"")
        resValue("string", "app_name", gameName)
        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
        }
    }

    buildFeatures {
        buildConfig = true
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }

    sourceSets {
        // The shared data pack (data/base/...) is bundled as assets: assets/base/pack.json, ...
        getByName("main").assets.srcDir(rootProject.file("../data"))
    }
}

val natives: Configuration by configurations.creating

dependencies {
    implementation(project(":game"))
    implementation(libs.gdx.backend.android)
    natives("com.badlogicgames.gdx:gdx-platform:${libs.versions.gdx.get()}:natives-arm64-v8a")
    natives("com.badlogicgames.gdx:gdx-platform:${libs.versions.gdx.get()}:natives-x86_64")
}

// libGDX ships its native libraries inside jars: unpack them into jniLibs/<abi>/ before packaging.
val copyAndroidNatives by tasks.registering {
    val jniDir = layout.projectDirectory.dir("src/main/jniLibs")
    inputs.files(natives)
    outputs.dir(jniDir)
    doLast {
        natives.files.forEach { jar ->
            val abi = jar.name.substringAfter("natives-").removeSuffix(".jar")
            copy {
                from(zipTree(jar))
                into(jniDir.dir(abi))
                include("*.so")
            }
        }
    }
}

tasks.matching { it.name.contains("JniLibFolders") }.configureEach {
    dependsOn(copyAndroidNatives)
}

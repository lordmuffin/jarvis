plugins {
    alias(libs.plugins.android.application)
    alias(libs.plugins.kotlin.android)
    alias(libs.plugins.kotlin.compose)
    alias(libs.plugins.kotlin.serialization)
    alias(libs.plugins.ksp)
}

android {
    namespace = "dev.jarvis"
    compileSdk = 34

    defaultConfig {
        applicationId = "dev.jarvis"
        minSdk = 31
        targetSdk = 34
        versionCode = 1
        versionName = "0.1.0"

        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"

        // The .tflite asset isn't gzip-compressed; LiteRT mmaps it directly.
        // Without this, the runtime cost on cold start spikes from APK decompression.
        androidResources {
            noCompress.add("tflite")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro",
            )
        }
        debug {
            // The smoke-test broadcast receiver is declared only in
            // src/debug/AndroidManifest.xml so it can't be triggered in release.
            isMinifyEnabled = false
            applicationIdSuffix = ".debug"
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }

    buildFeatures {
        compose = true
    }

    packaging {
        resources {
            excludes += "/META-INF/{AL2.0,LGPL2.1}"
        }
    }

    testOptions {
        unitTests {
            isIncludeAndroidResources = true
            isReturnDefaultValues = true
        }
    }

    // Room schema export — useful for diffing migrations.
    ksp {
        arg("room.schemaLocation", "$projectDir/schemas")
    }
}

dependencies {
    implementation(libs.androidx.core.ktx)
    implementation(libs.androidx.lifecycle.runtime.ktx)
    implementation(libs.androidx.lifecycle.service)
    implementation(libs.androidx.activity.compose)
    implementation(platform(libs.androidx.compose.bom))
    implementation(libs.androidx.compose.ui)
    implementation(libs.androidx.compose.ui.graphics)
    implementation(libs.androidx.compose.ui.tooling.preview)
    implementation(libs.androidx.compose.material3)
    implementation(libs.androidx.work.runtime.ktx)
    implementation(libs.androidx.room.runtime)
    implementation(libs.androidx.room.ktx)
    ksp(libs.androidx.room.compiler)
    implementation(libs.kotlinx.serialization.json)

    implementation(libs.litert)
    implementation(libs.litert.gpu)

    debugImplementation(libs.androidx.compose.ui.tooling)

    testImplementation(libs.junit)
    testImplementation(libs.truth)
    testImplementation(libs.robolectric)
    testImplementation(libs.mockk)
    testImplementation(libs.androidx.room.testing)
    testImplementation(libs.kotlinx.coroutines.test)

    androidTestImplementation(libs.androidx.junit)
}

// ---- Forbidden-import check -----------------------------------------------
//
// Phase 1 sovereignty: LiteRT only, never the legacy TF-Lite. Reject any module
// that re-introduces it. Runs on every build (cheap grep against the resolved
// runtime classpath).
val verifyForbiddenDependencies by tasks.registering {
    group = "verification"
    description = "Fail the build if org.tensorflow:tensorflow-lite* is on the classpath."
    val classpathProvider = configurations.named("releaseRuntimeClasspath")
    doLast {
        val forbidden = classpathProvider.get().incoming
            .resolutionResult
            .allDependencies
            .map { it.toString() }
            .filter { it.contains("org.tensorflow:tensorflow-lite") }
        if (forbidden.isNotEmpty()) {
            throw GradleException(
                "Forbidden dependency on classpath:\n  " + forbidden.joinToString("\n  ") +
                "\n\nPhase 1 uses LiteRT only (com.google.ai.edge.litert:*).\n" +
                "If a transitive dependency pulled this in, exclude it explicitly.",
            )
        }
    }
}

tasks.named("preBuild").configure {
    dependsOn(verifyForbiddenDependencies)
}

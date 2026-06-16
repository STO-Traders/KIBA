plugins {
    id("java")
    id("org.jetbrains.kotlin.jvm") version "1.9.25"
    id("org.jetbrains.intellij") version "1.17.4"
}

group = "com.stotraders"
version = "0.1.0"

repositories {
    mavenCentral()
}

// Build against IntelliJ Community 2024.1 (works in all JetBrains IDEs via the platform).
intellij {
    version.set("2024.1")
    type.set("IC")
    plugins.set(emptyList<String>())
}

tasks {
    patchPluginXml {
        sinceBuild.set("241")
        untilBuild.set("")
    }
    buildSearchableOptions {
        enabled = false
    }
}

kotlin {
    jvmToolchain(17)
}

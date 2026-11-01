package io.github.progliodario.aethermoor.core

import java.io.File
import org.junit.jupiter.api.Assertions.assertEquals
import org.junit.jupiter.api.Assertions.assertNotNull
import org.junit.jupiter.api.Assertions.assertNull
import org.junit.jupiter.api.Assertions.assertTrue
import org.junit.jupiter.api.Test

class PackTest {
    private val repoRoot = File(System.getProperty("aether.repoRoot") ?: error("aether.repoRoot is not set"))
    private val pack = loadBasePack(repoRoot)

    @Test
    fun manifest() {
        assertEquals("base", pack.manifest.id)
        assertEquals(1, pack.manifest.dataFormatVersion)
        assertEquals(listOf("it", "en"), pack.manifest.languages)
    }

    @Test
    fun localization() {
        assertEquals("Aethermoor", pack.text("it", "\$i18n:game.title"))
        assertEquals("Chronicles of Another World", pack.text("en", "\$i18n:game.subtitle"))
        assertEquals("Versione 0.1.0", pack.text("it", "\$i18n:ui.version", mapOf("version" to "0.1.0")))
        assertEquals("Pane", pack.text("it", "\$i18n:item.bread.name", mapOf("count" to 1L)))
        assertEquals("Pani", pack.text("it", "\$i18n:item.bread.name", mapOf("count" to 3L)))
        assertEquals("Bread", pack.text("en", "\$i18n:item.bread.name", mapOf("count" to 3L)))
    }

    @Test
    fun localizationFallsBackToTheKey() {
        assertEquals("no.such.key", pack.text("it", "\$i18n:no.such.key"))
        assertEquals("Chronicles of Another World", pack.text("fr", "\$i18n:game.subtitle"))
    }

    @Test
    fun xpTable() {
        assertEquals(50, pack.xpToNext(1))
        assertEquals(130, pack.xpToNext(2))
        assertEquals(47994, pack.xpToNext(98))
        assertEquals(0, pack.xpToNext(99))
        assertEquals(0, pack.xpToNext(0))
    }

    @Test
    fun missingPackReportsAnErrorInsteadOfThrowing() {
        val errors = ArrayList<String>()
        assertNull(loadPack(FileSystemPackSource(File(repoRoot, "data/does_not_exist")), errors))
        assertTrue(errors.isNotEmpty())
    }

    @Test
    fun basePackLoadsWithoutErrors() {
        val errors = ArrayList<String>()
        assertNotNull(loadPack(FileSystemPackSource(File(repoRoot, "data/base")), errors))
        assertEquals(emptyList<String>(), errors)
    }
}

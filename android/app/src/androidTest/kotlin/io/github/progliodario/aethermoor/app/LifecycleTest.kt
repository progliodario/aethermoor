package io.github.progliodario.aethermoor.app

import android.content.pm.ActivityInfo
import androidx.lifecycle.Lifecycle
import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.badlogic.gdx.ApplicationListener
import com.badlogic.gdx.Gdx
import com.badlogic.gdx.graphics.Texture
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertSame
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit

/**
 * The game on an emulator (item C4.2 of the operating program; `.github/workflows/nightly.yml` runs it on API 30 and 34, see
 * docs/design/performance.md): it starts and draws, turns, goes to the background and comes back, and it is still the same game
 * (neither the activity nor the game is created again). Its textures are managed, so a lost OpenGL context rebuilds them (risk R6).
 */
@RunWith(AndroidJUnit4::class)
class LifecycleTest {
    @Test
    fun theGameStartsTurnsPausesAndResumes() {
        ActivityScenario.launch(AndroidLauncher::class.java).use { scenario ->
            waitForFrames(START_FRAMES)
            var launcher: AndroidLauncher? = null
            var game: ApplicationListener? = null
            scenario.onActivity {
                launcher = it
                game = it.applicationListener
            }
            assertNotNull("the game runs", game)
            assertTrue("the textures are managed", managedTextures() > 0)

            scenario.onActivity { it.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_LANDSCAPE }
            waitForFrames(MORE_FRAMES)
            scenario.onActivity { it.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_SENSOR_PORTRAIT }
            waitForFrames(MORE_FRAMES)

            // to the background (the surface and the context may be lost) and back
            scenario.moveToState(Lifecycle.State.CREATED)
            scenario.moveToState(Lifecycle.State.RESUMED)
            waitForFrames(MORE_FRAMES)

            scenario.onActivity {
                assertSame("the activity is not created again", launcher, it)
                assertSame("the game is not created again", game, it.applicationListener)
            }
            assertTrue("the textures are still managed", managedTextures() > 0)
        }
    }

    /** Waits until the game has drawn [count] more frames. */
    private fun waitForFrames(count: Long) {
        val deadline = System.currentTimeMillis() + TIMEOUT_MS
        val start = frameId()
        while (frameId() - start < count) {
            check(System.currentTimeMillis() < deadline) { "the game drew ${frameId() - start} frames in ${TIMEOUT_MS / MS_PER_S} s" }
            Thread.sleep(POLL_MS)
        }
    }

    private fun frameId(): Long = Gdx.graphics?.frameId ?: -1L

    /** The managed textures of the game, counted on the thread of OpenGL. */
    private fun managedTextures(): Int {
        val latch = CountDownLatch(1)
        var count = 0
        Gdx.app.postRunnable {
            count = Texture.getNumManagedTextures()
            latch.countDown()
        }
        assertTrue("the thread of OpenGL answers", latch.await(TIMEOUT_MS, TimeUnit.MILLISECONDS))
        return count
    }

    private companion object {
        const val START_FRAMES = 30L
        const val MORE_FRAMES = 10L
        const val TIMEOUT_MS = 180_000L
        const val MS_PER_S = 1000L
        const val POLL_MS = 100L
    }
}

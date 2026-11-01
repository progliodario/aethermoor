package io.github.progliodario.aethermoor.app

import android.os.Bundle
import com.badlogic.gdx.backends.android.AndroidApplication
import com.badlogic.gdx.backends.android.AndroidApplicationConfiguration
import io.github.progliodario.aethermoor.core.GameInfo
import io.github.progliodario.aethermoor.game.AethermoorGame

class AndroidLauncher : AndroidApplication() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val config = AndroidApplicationConfiguration().apply {
            useImmersiveMode = true
            useAccelerometer = false
            useCompass = false
        }
        initialize(AethermoorGame(GameInfo(BuildConfig.GAME_NAME, BuildConfig.VERSION_NAME)), config)
    }
}

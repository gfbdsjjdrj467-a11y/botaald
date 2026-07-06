package com.botaald.app

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.botaald.app.databinding.ActivityMainBinding

class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
    }

    private fun setupUI() {
        binding.apply {
            textWelcome.text = "Добро пожаловать в BotaAld!"
            buttonAction.setOnClickListener {
                textMessage.text = "Приложение работает успешно!"
            }
        }
    }
}
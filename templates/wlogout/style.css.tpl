@import url("{{COLORS_FILE_PATH}}");

/* Structure only: wallpaper, icon geometry and motion stay app-owned. The
 * generated skin owns all surface styling and is imported last. */
* {
	transition: 20ms;
	background-image: none;
}

window {
	background-image: url("{{CURRENT_WALLPAPER_SYMLINK}}");
	background-size: cover;
	background-position: center;
	background-repeat: no-repeat;
}

button {
	background-repeat: no-repeat;
	background-position: center;
	background-size: 20%;
	animation: gradient_f 20s ease-in infinite;
	transition: all 0.3s cubic-bezier(.55, 0.0, .28, 1.682), box-shadow 0.2s ease-in-out, background-color 0.2s ease-in-out;
	-gtk-icon-effect: none;
}

button:focus, button:hover {
	background-size: 30%;
}

#lock {
    background-image: image(url("{{STATE_ROOT}}/dotfiles/current/icons/lock.svg"));
}

#logout {
    background-image: image(url("{{STATE_ROOT}}/dotfiles/current/icons/logout.svg"));
}

#suspend {
    background-image: image(url("{{STATE_ROOT}}/dotfiles/current/icons/suspend.svg"));
}

#hibernate {
    background-image: image(url("{{STATE_ROOT}}/dotfiles/current/icons/hibernate.svg"));
}

#shutdown {
    background-image: image(url("{{STATE_ROOT}}/dotfiles/current/icons/shutdown.svg"));
}

#reboot {
    background-image: image(url("{{STATE_ROOT}}/dotfiles/current/icons/reboot.svg"));
}

/* Generated skin appearance is imported LAST so its same-specificity paint
 * rules win the cascade. The palette import at the top keeps wlogout usable
 * with palette-only styling if the generated target is not present yet. */
@import url("appearance.css");

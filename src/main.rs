mod downloader;
mod models;

use gtk::prelude::*;
use gtk::{Application, ApplicationWindow, Button, Entry, Orientation, Box as GtkBox};
use glib::clone; // needed for clone! macro

fn main() {
    let app = Application::new(
        Some("com.wolf.player"),
        Default::default(),
    );

    app.connect_activate(|app| {
        let window = ApplicationWindow::new(app);
        window.set_title("WolfPlayer");
        window.set_default_size(600, 400);

        let vbox = GtkBox::new(Orientation::Vertical, 8);
        let url_entry = Entry::new();
        let add_btn = Button::with_label("Add");

        url_entry.set_placeholder_text(Some("Paste YouTube URL"));

  add_btn.connect_clicked(clone!(@weak url_entry => move |_| {
    let url = url_entry.text().to_string();
    if url.is_empty() {
        return;
    }

    glib::MainContext::default().spawn_local(async move {
match downloader::fetch_metadata(&url) {
            Ok(meta) => {
                println!("Title: {}", meta.title);
                println!("Uploader: {:?}", meta.uploader);
                println!("Duration: {:?}", meta.duration);
            }
            Err(e) => eprintln!("Error: {}", e),
        }
    });
}));


        vbox.add(&url_entry);
        vbox.add(&add_btn);
        window.add(&vbox);
        window.show_all();
    });

    app.run();
}

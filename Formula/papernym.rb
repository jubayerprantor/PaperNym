class Papernym < Formula
  include Language::Python::Virtualenv

  desc "Academic PDF renamer with scholarly metadata resolution"
  homepage "https://github.com/jubayerprantor/PaperNym"
  url "https://github.com/jubayerprantor/PaperNym/archive/refs/tags/v0.1.4.tar.gz"
  sha256 "0000000000000000000000000000000000000000000000000000000000000000" # Updated on release tag
  license "MIT"
  head "https://github.com/jubayerprantor/PaperNym.git", branch: "main"

  depends_on "python@3.11"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "PaperNym", shell_output("#{bin}/papernym --version")
    assert_match "Usage:", shell_output("#{bin}/papernym --help")
  end
end

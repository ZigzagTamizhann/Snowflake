{
  "blocks": {
    "languageVersion": 0,
    "blocks": [
      {
        "type": "setup",
        "id": "FDK1.LKT?WsTd.hlRa%^",
        "x": 255,
        "y": 36,
        "inputs": {
          "loop": {
            "block": {
              "type": "custom_if",
              "id": "z*~[tpTN=?yEi?=J5J.r",
              "inputs": {
                "IF0": {
                  "block": {
                    "type": "Button",
                    "id": "[]Uf8JASi1,l@zA4jLvY",
                    "fields": {
                      "button": "ButtonL",
                      "value": "0"
                    }
                  }
                },
                "DO0": {
                  "block": {
                    "type": "led_control",
                    "id": "xJf2#5J,A8K$C5v#kT}B",
                    "fields": {
                      "COLOR": "#55ff17"
                    },
                    "inputs": {
                      "value": {
                        "shadow": {
                          "type": "math_number",
                          "id": "V39gO`wS^xD4z:J,36ud",
                          "fields": {
                            "NUM": 1
                          }
                        }
                      }
                    },
                    "next": {
                      "block": {
                        "type": "led_control",
                        "id": "C*=![zHp-i5LB,#ecoI|",
                        "fields": {
                          "COLOR": "#000000"
                        },
                        "inputs": {
                          "value": {
                            "shadow": {
                              "type": "math_number",
                              "id": "19[B;d5GH*0jDv*.)C)3",
                              "fields": {
                                "NUM": 2
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              },
              "next": {
                "block": {
                  "type": "custom_else",
                  "id": ";nPpwvj[M!8QloSnk$=.",
                  "inputs": {
                    "DO": {
                      "block": {
                        "type": "led_control",
                        "id": "lX3U|cza+!j48PKI]F,p",
                        "fields": {
                          "COLOR": "#000000"
                        },
                        "inputs": {
                          "value": {
                            "shadow": {
                              "type": "math_number",
                              "id": "T{n0+09??St{KyM*1sv/",
                              "fields": {
                                "NUM": 1
                              }
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    ]
  },
  "selectedKit": "subo"
}